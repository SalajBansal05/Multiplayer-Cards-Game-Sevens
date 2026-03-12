function cardToImage(card) {
  const rankMap = {
    A: "1",
    K: "13",
    Q: "12",
    J: "11"
  };

  const suitMap = {
    H: "hearts",
    S: "spades",
    D: "diamonds",
    C: "clubs"
  };

  let rank = card.slice(0, -1);
  let suit = card.slice(-1);

  if (rankMap[rank]) {
    rank = rankMap[rank];
  }

  suit = suitMap[suit];

  return `${rank}_of_${suit}.svg`;
}

function Card({ card, onClick, playable }) {

  const imageName = cardToImage(card);

  return (
    <img
      src={`/cards/${imageName}`}
      alt={card}
      width="80"
      onClick={onClick}
      style={{
        cursor:onClick ? "pointer":"default",
        opacity: playable === false ? 0.4 : 1,
        pointerEvents: playable === false ? "none" : "auto" // Add this!
      }}
    />
  );

}

export default Card;