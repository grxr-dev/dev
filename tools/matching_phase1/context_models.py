"""Bounded decoded-operation checks on virtual bytes/stack; no guest or host C execution."""
import itertools
import re
from nul_count_pilot import decode

MASK=0xffffffff
CONTEXT=0x4000
INPUT=0x5000
STACK=0x8000
RETURN=0x9000
PAIR=0x6000
WRITTEN={0:4,4:4,8:4,12:4,16:4,24:2}


def trace(rows,initial,*,first=0,second=0,pair=(0,0),initialize_pair=True,alignment=0,
          protocol=None,dispatch_result=0,dispatch_words=None,forward_result=0,forward_pair=None,forward_read_offsets=()):
    context=CONTEXT+alignment
    registers={f'r{index}':0xabc00000+index for index in range(13)}
    registers.update(r0=context,r1=INPUT,sp=STACK,lr=RETURN)
    pair_address=PAIR+alignment
    if protocol=='context_accept':registers.update(r1=first,r2=second)
    elif protocol=='pair_forward':registers['r0']=pair_address
    elif protocol is not None:raise ValueError('unknown protocol scenario')
    preserved={name:registers[name] for name in ['sp',*[f'r{index}' for index in range(4,12)]]}
    memory={context+index:value for index,value in enumerate(initial)}
    calls=[];writes=[];reads=[];call_states=[];frame=None;frame_limit=None;scratch=None;maximum_stack=0;zero=False;nzcv=None
    program={pc:(op,args) for pc,op,args in rows};pc=rows[0][0]

    def value(token):
        return int(token[1:],0)&MASK if token.startswith('#') else registers[token]

    def read(address,width):
        if address%width or any(address+index not in memory for index in range(width)):
            raise ValueError('uninitialized/unaligned virtual read')
        reads.append((address,width))
        return sum(memory[address+index]<<(8*index) for index in range(width))

    def write(address,width,number):
        if address%width or not (context<=address<=context+len(initial)-width or registers['sp']<=address<=STACK-width or protocol=='pair_forward' and pair_address<=address<=pair_address+8-width):
            raise ValueError('outside virtual context/owned stack')
        writes.append((address,width,number&((1<<(8*width))-1)))
        for index in range(width):memory[address+index]=(number>>(8*index))&255

    def finish(target):
        if target!=RETURN or any(registers[name]!=number for name,number in preserved.items()):
            raise ValueError('callee-saved register/SP/return mismatch')
        return {'return':registers['r0'],'context':bytes(memory[context+index] for index in range(len(initial))),
                'calls':calls,'writes':writes,'reads':reads,'stack_bytes':maximum_stack,'call_states':call_states,'nzcv':nzcv,
                'output_pair_bytes':[memory.get(pair_address+index) for index in range(8)]}

    for step in range(64):
        if pc not in program:raise ValueError('escaped bounded context code')
        op,args=program[pc];args=args.replace('fp','r11').replace('ip','r12');next_pc=pc+4
        if op not in ('beq','bne') and op.endswith(('eq','ne')):
            condition=op[-2:];op=op[:-2]
            if zero!=(condition=='eq'):pc=next_pc;continue
        if op=='mov':
            destination,source=args.split(', ');registers[destination]=value(source)
        elif op in ('add','sub'):
            destination,left,right=args.split(', ')
            if destination=='sp' and op=='sub':frame_limit=registers['sp']
            registers[destination]=(value(left)+(value(right) if op=='add' else -value(right)))&MASK
            if destination=='sp' and op=='sub':frame=registers['sp']
        elif op in ('orr','bic'):
            destination,left,right=args.split(', ')
            registers[destination]=(value(left)|(value(right)))&MASK if op=='orr' else value(left)&(~value(right)&MASK)
        elif op in ('str','strh','ldr'):
            match=re.fullmatch(r'(r\d+), \[(r\d+|sp)(?:, #(0x[0-9a-f]+|\d+))?\]',args)
            if not match:raise ValueError('unsupported context memory operand')
            register,base,offset=match.groups();address=registers[base]+int(offset or '0',0)
            if op=='ldr':registers[register]=read(address,4)
            else:write(address,2 if op=='strh' else 4,registers[register])
        elif op in ('push','pop'):
            names=args[1:-1].split(', ')
            if op=='push':
                registers['sp']-=4*len(names)
                for index,name in enumerate(names):write(registers['sp']+4*index,4,registers[name])
            else:
                values=[read(registers['sp']+4*index,4) for index in range(len(names))]
                registers['sp']+=4*len(names)
                for name,number in zip(names,values):
                    if name=='pc':return finish(number)
                    registers[name]=number
        elif op=='ldm':
            base,names=args.split(', ',1);names=names[1:-1].split(', ');address=registers[base]
            values=[read(address+4*index,4) for index in range(len(names))]
            for name,number in zip(names,values):registers[name]=number
        elif op=='cmp':
            left,right=args.split(', ');left=value(left);right=value(right);difference=(left-right)&MASK;zero=left==right
            nzcv=(difference>>31,int(zero),int(left>=right),int(bool((left^right)&(left^difference)&0x80000000)))
        elif op in ('b','beq','bne'):
            if op=='b' or zero==(op=='beq'):next_pc=value(args)
        elif op=='bl':
            target=value(args)
            if protocol=='context_accept' and target==0x0200a464:
                arguments=tuple(registers[f'r{index}'] for index in range(4))
                if arguments!=(context,6,second,first):raise ValueError('dispatcher ABI mismatch')
                calls.append((target,*arguments));before=bytes(memory[context+index] for index in range(len(initial)))
                for offset,number in (dispatch_words or {}).items():write(context+offset,4,number)
                call_states.append({'before':before,'after':bytes(memory[context+index] for index in range(len(initial)))})
                result=dispatch_result
            elif protocol=='pair_forward' and target==0x0200aee8:
                scratch=registers['r0']
                if frame_limit is None or not registers['sp']<=scratch<=frame_limit-68:raise ValueError('scratch reservation/ABI mismatch')
                calls.append((target,'scratch'))
                for offset,width in WRITTEN.items():write(scratch+offset,width,14 if offset==16 else 0)
                result=0
            elif protocol=='pair_forward' and target==0x0200ad94:
                arguments=tuple(registers[f'r{index}'] for index in range(4))
                if scratch is None or arguments!=(scratch,INPUT,pair_address,0):raise ValueError('forward producer ABI mismatch')
                calls.append((target,'scratch',INPUT,pair_address,0))
                call_states.append({'scratch':[(index,memory[scratch+index]) for index in range(68) if scratch+index in memory]})
                for offset in forward_read_offsets:read(scratch+offset,4)
                if forward_pair is not None:
                    write(pair_address,4,forward_pair[0]);write(pair_address+4,4,forward_pair[1])
                result=forward_result
            elif protocol is not None:raise ValueError('unknown protocol callee')
            elif target==0x0200acd0:
                if frame is None or registers['r0']!=frame or registers['r1']!=INPUT:
                    raise ValueError('pair producer ABI mismatch')
                calls.append((target,'frame',INPUT))
                if first and initialize_pair:
                    write(frame,4,pair[0]);write(frame+4,4,pair[1])
                result=first
            elif target==0x0200ac04:
                if registers['r0']!=context or (registers['r1'],registers['r2'])!=pair:
                    raise ValueError('pair consumer ABI mismatch')
                calls.append((target,context,*pair));result=second
            else:raise ValueError('unknown opaque callee')
            for index in range(4):registers[f'r{index}']=0xd00d0000+index
            registers['r0']=result&MASK;registers['lr']=next_pc
        elif op=='bx':return finish(value(args))
        else:raise ValueError('unsupported context operation '+op)
        maximum_stack=max(maximum_stack,STACK-registers['sp']);pc=next_pc
    raise ValueError('bounded context instruction budget')


def initialized(initial):
    result=bytearray(initial)
    for offset,width in WRITTEN.items():result[offset:offset+width]=(14 if offset==16 else 0).to_bytes(width,'little')
    return bytes(result)


def verify(kind,original,compiled,address):
    left=decode(original,address);right=decode(compiled,address);count=0
    if kind=='context_init':
        for seed,alignment in itertools.product(range(128),(0,4,8,12)):
            initial=bytes((seed+index*37)&255 for index in range(32))
            for rows in (left,right):
                result=trace(rows,initial,alignment=alignment)
                if result['context']!=initialized(initial) or result['calls'] or result['stack_bytes'] or result['return']!=CONTEXT+alignment:
                    raise ValueError('initializer field/return/control mismatch')
                if {(at-CONTEXT-alignment,width) for at,width,_ in result['writes']}!=set(WRITTEN.items()):
                    raise ValueError('initializer writes outside verified fields')
            count+=1
    elif kind=='context_prepare':
        for first,second,pair,alignment in itertools.product((0,1,0xffffffff,0x80000000),(0,1,0xffffffff,0x80000000),
                ((0,0),(1,2),(0xffffffff,0x80000000),(0x12345678,0x87654321),(0,0xffffffff)),(0,4,8,12)):
            initial=bytes(range(32));before=trace(left,initial,first=first,second=second,pair=pair,alignment=alignment)
            after=trace(right,initial,first=first,second=second,pair=pair,alignment=alignment)
            expected=int(first!=0 and second!=0)
            if before['return']!=expected or after['return']!=expected or before['calls']!=after['calls'] or len(before['calls'])!=(2 if first else 1):
                raise ValueError('conditional pair protocol/return mismatch')
            if before['context']!=initial or after['context']!=initial or before['stack_bytes']!=16 or after['stack_bytes']!=16:
                raise ValueError('wrapper local effects/frame mismatch')
            count+=1
    elif kind=='context_accept':
        for first,second,result,flags,mutate,alignment in itertools.product((0,1,0x80000000,0xffffffff),(0,1,0x12345678,0xffffffff),
                (0,1,0x80000000,0xffffffff),(0,0x10,0x20,0x30,0x80000000,0xffffffff),(False,True),(0,4)):
            initial=bytearray(range(64));initial[12:16]=flags.to_bytes(4,'little');initial=bytes(initial)
            effects={12:flags^0xa5a5a5a5,20:0x2468,8:0x1234,44:0x5678,48:0x9abc} if mutate else {}
            expected=bytearray(initial)
            if first:
                for offset,number in {8:first,44:first,48:second}.items():expected[offset:offset+4]=number.to_bytes(4,'little')
                for offset,number in effects.items():expected[offset:offset+4]=number.to_bytes(4,'little')
                if result:
                    flags_after=int.from_bytes(expected[12:16],'little')
                    expected[12:16]=((flags_after|0x10)&~0x20).to_bytes(4,'little')
            traces=[trace(rows,initial,protocol=kind,first=first,second=second,dispatch_result=result,dispatch_words=effects,alignment=alignment) for rows in (left,right)]
            for checked in traces:
                if checked['return']!=int(first!=0 and result!=0) or checked['context']!=bytes(expected) or len(checked['calls'])!=int(first!=0):
                    raise ValueError('dispatch pre/post fields or return mismatch')
            if traces[0]['calls']!=traces[1]['calls'] or traces[0]['call_states']!=traces[1]['call_states'] or traces[0]['nzcv']!=traces[1]['nzcv']:
                raise ValueError('dispatcher arguments/state/flags differ')
            count+=1
    elif kind=='pair_forward':
        expected_scratch=initialized(bytes(68))
        initialized_offsets={offset+index for offset,width in WRITTEN.items() for index in range(width)}
        for result,output,alignment in itertools.product((0,1,0x80000000,0xffffffff),(None,(0,0),(0xffffffff,0x80000000)),(0,4,8,12)):
            traces=[trace(rows,bytes(32),protocol=kind,forward_result=result,forward_pair=output,alignment=alignment) for rows in (left,right)]
            expected_output=[None]*8 if output is None else list(b''.join(number.to_bytes(4,'little') for number in output))
            for checked in traces:
                if checked['return']!=int(result!=0) or checked['output_pair_bytes']!=expected_output or len(checked['calls'])!=2:
                    raise ValueError('forward output/return/call count mismatch')
                if checked['call_states']!=[{'scratch':[(index,expected_scratch[index]) for index in sorted(initialized_offsets)]}]:
                    raise ValueError('scratch initialized extent differs')
            if traces[0]['calls']!=traces[1]['calls'] or traces[0]['nzcv']!=traces[1]['nzcv']:
                raise ValueError('forwarded arguments/flags differ')
            count+=1
    else:raise ValueError('unknown context model')
    return {'status':'PASS_BOUNDED_MODEL','cases':count,'count_kind':'finite_cases','independent_cpu_emulator':False,
            'formatter_or_external_effects_proved':False,'evidence_scope':'ordinary memory effects' if kind=='context_init' else 'conditional opaque protocol only'}
