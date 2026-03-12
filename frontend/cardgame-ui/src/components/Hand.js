import Card from "./Card";

import React from 'react'

const Hand = ({ cards, playCard, isMyTurn, isPlayable }) => {
  return (
    <div className="hand">
      {cards.map((card) => {
        const playable = isPlayable(card);
        return (
          <div key={card} className="card-wrapper">
            <Card
              card={card}
              onClick={isMyTurn && playable ? () => playCard(card) : null}
              playable={playable}
            />
          </div>
        );
      })}
    </div>
  )
}

export default Hand
