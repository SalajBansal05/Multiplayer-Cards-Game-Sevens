function HowToPlay({ onClose }) {
  return (
    <div className="how-to-play-overlay" onClick={onClose}>
      <div
        className="how-to-play-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="how-to-play-header">
          <div>
            <span className="how-to-play-suit">♥</span>
            <h2>How to Play</h2>
          </div>

          <button
            className="how-to-play-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="how-to-play-content">
          <div className="rule">
            <span className="rule-number">1</span>
            <div>
              <h3>Start with 7♥</h3>
              <p>
                The player holding the 7 of hearts starts the game,
                and the first card played must be 7♥.
              </p>
            </div>
          </div>

          <div className="rule">
            <span className="rule-number">2</span>
            <div>
              <h3>Build the suits</h3>
              <p>
                Add the next higher or lower card to an existing
                suit pile. A new suit starts with its 7.
              </p>
            </div>
          </div>

          <div className="rule">
            <span className="rule-number">3</span>
            <div>
              <h3>Pass when needed</h3>
              <p>
                If you have no legal move, you must pass your turn.
              </p>
            </div>
          </div>

          <div className="rule">
            <span className="rule-number">4</span>
            <div>
              <h3>Empty your hand</h3>
              <p>
                The first player to play all their cards wins the game.
              </p>
            </div>
          </div>

          <div className="rule">
            <span className="rule-number">5</span>
            <div>
              <h3>Score the remaining cards</h3>
              <p>
                Your score is the total value of the cards left in
                your hand.
              </p>
            </div>
          </div>

          <div className="rule">
            <span className="rule-number">6</span>
            <div>
              <h3>Lowest score wins</h3>
              <p>
                The player with the lowest score wins.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HowToPlay;