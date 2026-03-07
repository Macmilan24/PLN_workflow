!(import! &self (library lib_import))
!(git-import! "https://github.com/trueagi-io/PLN.git")
!(import! &self (library PLN lib_pln))

!(bind! &bubble (new-space))

!(bind! &history (new-space))
!(import! &history metta_kbs/galaxy_history.metta)

!(bind! &masterlist (new-space))


(= (Generate-Master-List $max_steps)
   (let* (
      ($initial_kb (collapse (match &bubble $fact $fact)))
      
      (($tasks $beliefs) (PLN.Derive $initial_kb $initial_kb $max_steps))
   )
   (collapse 
      (let (Sentence ((Inheritance $node UserIntent) (stv $s $c)) $ev) (superpose $beliefs)
           ($node $s $c) 
      )
   ))
)


(= (Get-Relevance $tool)
   (let $res (collapse (match &masterlist (Sentence ((Relevance $tool) $stv) $ev) $stv))
        (if (== $res ())
            (stv 0.10 0.50)
            (car-atom $res))))


(= (Predict-Next $current_tool)
   (match &history (Sentence ((Implication $current_tool $next_tool) $H_stv) $Hev)
        (let* (
             ($R_stv (Get-Relevance $next_tool))
             
             ((stv $rev_s $rev_c) (Truth_Revision $H_stv $R_stv))
            )
            ($next_tool $rev_s $rev_c)
        )
   )
)