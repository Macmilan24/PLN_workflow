(= (expand-vertical $node $global_space $bubble_space)
(superpose 
        (
            (match $global_space 
         (Sentence ((Inheritance $node $parent) $stv) $ev)
         (add-atom $bubble_space (Sentence ((Inheritance $node $parent) $stv) $ev))
      )

      (match $global_space 
         (Sentence ((Inheritance $child $node) $stv) $ev)
         (add-atom $bubble_space (Sentence ((Inheritance $child $node) $stv) $ev))
      )
        )
    )

    (add-atom $bubble_space (Sentence ((Inheritance $A $B) $stv) $ev))

)

(= (expand-horizontal $node $global_space $bubble_space)
        (superpose
            (
                (match $global_space
         (Sentence ((Implication $node $next) $stv) $ev)
         (add-atom $bubble_space (Sentence ((Implication $node $next) $stv) $ev))
      )
      (match $global_space
         (Sentence ((Implication $prev $node) $stv) $ev)
         (add-atom $bubble_space (Sentence ((Implication $prev $node) $stv) $ev))
      )
            )
        )

)

(= (extract-context-for-node $node $global $bubble)
   (superpose (
      (expand-vertical $node $global $bubble)
      (expand-horizontal $node $global $bubble)
   ))
)