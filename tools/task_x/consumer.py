"""ROM-free offline model of mode-0 numeric consumption with policy +31C=2.
No runtime import: expected is offline metadata, never a recognizer input.
"""
class Consumer:
    def __init__(self):
        self.prefix=[];self.prefix_accessor=[]
    def consume(self, groups, expected):
        # Original worker appends group 0 and replaces group 1 (15-code loops).
        self.prefix.extend(groups[0]['codes'][:15])
        self.prefix_accessor.extend(groups[0]['accessor_codes'][:15])
        primary=(self.prefix+groups[1]['codes'][:15])[:16]
        secondary=(self.prefix_accessor+groups[1]['accessor_codes'][:15])[:16]
        values=[c-48 for c in primary];alt=[c-48 for c in secondary]
        chosen=values.copy();substituted=[]
        if 0<=expected<10 and len(values)==1 and alt[0]==expected and alt[0]!=1:
            chosen[0]=alt[0];substituted.append(0)
        elif expected>=10 and len(values)==2:
            if alt[0]==expected//10 and alt[0]!=1:
                chosen[0]=alt[0];substituted.append(0)
            # Preserve the original unusual guard on the FIRST accessor digit.
            if alt[1]==expected%10 and alt[0]!=1:
                chosen[1]=alt[1];substituted.append(1)
        def number(ds):
            n=0
            for d in ds:n=((n*10+d+2**31)%2**32)-2**31
            return n if 0<=n<100 else 65535
        return {'primary_codes':primary,'accessor_codes':secondary,
                'primary_numeric':number(values),'original_consumer_numeric':number(chosen),
                'substituted_positions':substituted,'offline_target_match':number(chosen)==expected,
                'target_code_occurs_anywhere':48+expected in primary+secondary if 0<=expected<10 else None,
                'ranked_candidate_set_exists':False}

def test():
    def groups(a,b='',prefix='',prefix_alt=''):
        return [dict(codes=list(map(ord,prefix)),accessor_codes=list(map(ord,prefix_alt))),dict(codes=list(map(ord,a)),accessor_codes=list(map(ord,b or a)))]
    assert Consumer().consume(groups('51','47'),7)['original_consumer_numeric']==51
    assert Consumer().consume(groups('4','9'),9)['original_consumer_numeric']==9
    assert Consumer().consume(groups('7','1'),1)['original_consumer_numeric']==7
    assert Consumer().consume(groups('23','19'),19)['original_consumer_numeric']==23
    assert Consumer().consume(groups('23','49'),49)['original_consumer_numeric']==49
    c=Consumer();assert c.consume(groups('2','2','1','1'),12)['original_consumer_numeric']==12
    assert c.consume(groups('3','3'),13)['original_consumer_numeric']==13
    assert Consumer().consume(groups('123'),1)['original_consumer_numeric']==65535
    print('PASS: positional consumption, prefix retention, conditional substitution, excluded 1, two-digit guard and invalid value')
if __name__=='__main__':test()
