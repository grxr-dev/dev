"""Reuse bounded Phase0 decoded-operation models, not CPU/guest execution."""
import itertools
import struct
from nul_count_pilot import decode, cases as count_cases, verify_case as count_check
from suffix_caller_pilot import cases as suffix_cases, verify_case as suffix_check
from input_parent_pilot import split_pool as parent_pool, parent_trace
from pointer_helper_pilot import split_pool as format_pool, helper_trace
from bounded_pilot import bit_origins


def verify(kind, original, compiled, address, counter):
    if kind in ('context_init','context_prepare'):
        from context_models import verify as context_check
        return context_check(kind,original,compiled,address)
    if kind == 'zero':
        for body in (original,compiled):
            if [(op,args) for _,op,args in decode(body,address)] != [('mov','r0, #0'),('bx','lr')]:
                raise ValueError('constant-return behavior changed')
        count=1
    elif kind == 'byte_exchange':
        expected=['x'+str(index) for index in [*range(8,16),*range(8)]]+[0]*16
        for body in (original,compiled):
            rows=[{'mnemonic':op,'operands':args} for _,op,args in decode(body,address)]
            if bit_origins(rows)!=expected:raise ValueError('bit-origin map differs')
        count=2**32
    elif kind in ('nul_count','suffix'):
        left=decode(original,address);right=decode(compiled,address)
        count=0
        cases=count_cases() if kind=='nul_count' else suffix_cases()
        for data,alignment in cases:
            if kind=='nul_count':count_check(left,right,data,alignment)
            else:suffix_check(left,right,counter,data,alignment)
            count+=1
    elif kind == 'context_parent':
        left,left_pool=parent_pool(original);right,right_pool=parent_pool(compiled)
        count=0
        for predicate,(start,end),header in itertools.product((0,1),((0,0),(4,40),(0x100,0x80),(0xfffffff0,0x10)),(0,0xffffffff,0x12345678)):
            scenario=dict(predicate=predicate,start=start,end=end,header=header,prepare_result=0,read_result=0)
            before=parent_trace(left,left_pool,**scenario);after=parent_trace(right,right_pool,**scenario)
            expected=header>>8 if predicate else (end-start)&0xffffffff
            if before['return']!=expected or after['return']!=expected or before['calls']!=after['calls']:
                raise ValueError('conditional parent ABI/control mismatch')
            count+=1
    elif kind == 'format_alias':
        left,left_pool=format_pool(original);right,right_pool=format_pool(compiled)
        count=0
        for pointer,incoming,result in itertools.product((0x5000,0x5001),(0,0xffffffff,0x1234),(0,1,0xffffffff,0xdeadbeef)):
            before=helper_trace(left,left_pool,pointer,incoming,result)
            after=helper_trace(right,right_pool,pointer,incoming,result)
            if before['return']!=0x020dcbb4 or after['return']!=before['return'] or before['call']!=after['call'] or before['call']!=[0x020dcbb4,pointer,0x65]:
                raise ValueError('fixed alias/opaque call arguments differ')
            count+=1
    else:raise ValueError('unregistered bounded behavior model')
    return {'status':'PASS_BOUNDED_MODEL','cases':count,'count_kind':'symbolic_input_words' if kind=='byte_exchange' else 'finite_cases',
            'independent_cpu_emulator':False,'formatter_or_external_effects_proved':False}
