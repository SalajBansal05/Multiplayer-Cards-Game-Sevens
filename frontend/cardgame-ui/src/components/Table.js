import Pile from './Pile'

function Table({ piles }) {
  return (
    <div className="table">

      <div>
        <h3>Hearts</h3>
        <Pile suit="H" {...piles.hearts} />
      </div>

      <div>
        <h3>Spades</h3>
        <Pile suit="S" {...piles.spades} />
      </div>

      <div>
        <h3>Diamonds</h3>
        <Pile suit="D" {...piles.diamonds} />
      </div>

      <div>
        <h3>Clubs</h3>
        <Pile suit="C" {...piles.clubs} />
      </div>

    </div>
  );
}

export default Table
