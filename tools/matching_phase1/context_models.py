"""Bounded decoded-operation checks on virtual bytes/stack; no guest or host C execution."""
import itertools
import re
from nul_count_pilot import decode

MASK=0xffffffff
CONTEXT=0x4000
INPUT=0x5000
STACK=0x8000
RETURN=0x9000
WRITTEN={0:4,4:4,8:4,12:4,16:4,24:2}


def trace(rows,initial,*,first=0,second=0,pair=(0,0),initialize_pair=True,alignment=0):
    context=CONTEXT+alignment
    registers={f'r{index}':0xabc00000+index for index in range(13)}
    registers.update(r0=context,r1=INPUT,sp=STACK,lr=RETURN)
    preserved={name:registers[name] for name in ['sp',*[f'r{index}' for index in range(4,12)]]}
    memory={context+index:value for index,value in enumerate(initial)}
    calls=[];writes=[];reads=[];frame=None;maximum_stack=0;zero=False
    program={pc:(op,args) for pc,op,args in rows};pc=rows[0][0]

    def value(token):
        return int(token[1:],0)&MASK if token.startswith('#') else registers[token]

    def read(address,width):
        if address%width or any(address+index not in memory for index in range(width)):
            raise ValueError('uninitialized/unaligned virtual read')
        reads.append((address,width))
        return sum(memory[address+index]<<(8*index) for index in range(width))

    def write(address,width,number):
        if address%width or not (context<=address<=context+len(initial)-width or registers['sp']<=address<=STACK-width):
            raise ValueError('outside virtual context/owned stack')
        writes.append((address,width,number&((1<<(8*width))-1)))
        for index in range(width):memory[address+index]=(number>>(8*index))&255

    def finish(target):
        if target!=RETURN or any(registers[name]!=number for name,number in preserved.items()):
            raise ValueError('callee-saved register/SP/return mismatch')
        return {'return':registers['r0'],'context':bytes(memory[context+index] for index in range(len(initial))),
                'calls':calls,'writes':writes,'reads':reads,'stack_bytes':maximum_stack}

    for step in range(64):
        if pc not in program:raise ValueError('escaped bounded context code')
        op,args=program[pc];next_pc=pc+4
        if op not in ('beq','bne') and op.endswith(('eq','ne')):
            condition=op[-2:];op=op[:-2]
            if zero!=(condition=='eq'):pc=next_pc;continue
        if op=='mov':
            destination,source=args.split(', ');registers[destination]=value(source)
        elif op in ('add','sub'):
            destination,left,right=args.split(', ')
            registers[destination]=(value(left)+(value(right) if op=='add' else -value(right)))&MASK
            if destination=='sp' and op=='sub':frame=registers['sp']
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
            left,right=args.split(', ');zero=value(left)==value(right)
        elif op in ('b','beq','bne'):
            if op=='b' or zero==(op=='beq'):next_pc=value(args)
        elif op=='bl':
            target=value(args)
            if target==0x0200acd0:
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
    else:raise ValueError('unknown context model')
    return {'status':'PASS_BOUNDED_MODEL','cases':count,'count_kind':'finite_cases','independent_cpu_emulator':False,
            'formatter_or_external_effects_proved':False,'evidence_scope':'ordinary memory effects' if kind=='context_init' else 'opaque pair protocol only'}
