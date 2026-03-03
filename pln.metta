!(import! &self (library lib_import))
!(git-import! "https://github.com/trueagi-io/PLN.git")
!(import! &self (library PLN lib_pln))

!(import! &self kb)


; !(bind! &kb (new-space))

; (= (STV A) (stv 0.5 0.5))
; (= (STV B) (stv 0.5 0.5))
; (= (STV C) (stv 0.5 0.5))


; !(add-atom &kb (Sentence ((Implication A B) (stv 1.0 1.0)) (1)))
; !(add-atom &kb (Sentence ((Implication B C) (stv 1.0 1.0)) (2)))

; !(let $kb (collapse (match &kb $fact $fact))
;     (PLN.Query $kb (Implication A C)))

!(PLN.Query (KB) (Implication Start STAR))


