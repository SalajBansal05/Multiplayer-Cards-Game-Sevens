import './App.css';
import {useEffect, useState} from "react"
import Hand from './components/Hand';
import Table from './components/Table';
import Notification from "./components/Notification";
import HowToPlay from "./components/HowToPlay";

function generateUUID() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);

  // UUID v4
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;

  return [...bytes]
    .map((byte, index) => {
      const hex = byte.toString(16).padStart(2, "0");

      if (index === 4 || index === 6 || index === 8 || index === 10) {
        return "-" + hex;
      }

      return hex;
    })
    .join("");
}

function getPlayerToken() {
  let token = localStorage.getItem("player_token");

  if (!token) {
    token = generateUUID();
    localStorage.setItem("player_token", token);
  }

  return token;
}


function App() {
  const [socket, setSocket] = useState(null);
  
  const [piles, setPiles] = useState({
    hearts: {low:null, high: null},
    spades: {low:null, high: null},
    diamonds: {low:null, high: null},
    clubs: {low:null, high: null},
  });

  const [screen, setScreen] = useState(() => {
    return localStorage.getItem("active_room") ? "game" : "lobby";
  });

  const [roomCode, setRoomCode] = useState(() => {
    return localStorage.getItem("active_room") || "";
  });
  const [roomInput, setRoomInput] = useState("");
  const [error, setError] = useState("");
  const [gameStarted, setGameStarted] = useState(false);
  const [host, setHost] = useState(null);
  const [showRules, setShowRules] = useState(false);

  const [displayName, setDisplayName] = useState(
    localStorage.getItem("display_name") || ""
  );

  const [playerNames, setPlayerNames] = useState({});

  const [paused, setPaused] = useState(false);
  const [disconnectedPlayer, setDisconnectedPlayer] = useState(null);
  const [timeoutExpired, setTimeoutExpired] = useState(false);
  const [gameEnded, setGameEnded] = useState(false);
  
  const [hand, setHand] = useState([]);
  
  const [currentTurn, setCurrentTurn] = useState(null);
  
  const [playerId, setPlayerId] = useState(null);
  
  const isMyTurn = playerId === currentTurn;

  const [counts, setCounts] = useState({});

  const [players, setPlayers] = useState([]);

  const [playersPlayingAgain, setPlayersPlayingAgain] = useState([]);

  const [scores, setScores] = useState({});

  const [winner, setWinner] = useState(null);

  async function createRoom() {
    const token = getPlayerToken();

    try {
      const response = await fetch(
        `http://${window.location.hostname}:8000/api/rooms/create/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token: token,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        if (data.room_id) {
          setError(
            `${data.error} Room: ${data.room_id}`
          );
        } else {
          setError(data.error || "Could not create game.");
        }

        return;
      }

      setError("");
      setRoomCode(data.room_id);
      localStorage.setItem("active_room", data.room_id);
      setScreen("game");

    } catch (error) {
      console.error(error);
      setError("Could not connect to the server.");
    }
  }

  function getDisplayName(player) {
    return playerNames[player] || player;
  }

  async function copyRoomCode() {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(roomCode);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = roomCode;

        textArea.style.position = "fixed";
        textArea.style.opacity = "0";

        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
      }

      setError("Room code copied.");
    } catch (error) {
      console.error(error);
      setError("Could not copy room code.");
    }
  }

  function joinRoom() {
    const code = roomInput.trim().toUpperCase();

    if (!code) {
      setError("Please enter a room code.");
      return;
    }

    setError("");
    localStorage.setItem("active_room", code);
    setRoomCode(code);
    setScreen("game");
  }

  function leaveGame() {
    if (!socket) return;

    socket.send(
      JSON.stringify({
        action: "leave_room"
      })
    );

    localStorage.removeItem("active_room");

    setRoomCode("");
    setRoomInput("");
    setGameStarted(false);
    setHost(null);
    setScreen("lobby");
  }

  function endGame() {
    if (!socket) return;

    socket.send(
      JSON.stringify({
        action: "end_game"
      })
    );
  }

  function passTurn(){
    if (!socket) return;
  
    socket.send(
      JSON.stringify({
        action: "pass"
      })
    );
  
  }

  const startGame = () => {
      socket.send(JSON.stringify({
          action: "start_game"
      }));
  };

  function rematch(){
    socket.send(JSON.stringify({
      action: "rematch"
    }))

  }

  useEffect(() => {
    if (!error) return;

    const timer = setTimeout(() => {
      setError("");
    }, 3500);

    return () => clearTimeout(timer);
  }, [error]);

  useEffect(() => {
    if (displayName.trim()) {
      localStorage.setItem("display_name", displayName.trim());
    }
  }, [displayName]);

  useEffect(() => {
    if (screen !== "game" || !roomCode) {
      return;
    }

    const playerToken = getPlayerToken();

    const encodedName = encodeURIComponent(displayName.trim());

    const ws = new WebSocket(
      `ws://${window.location.hostname}:8000/ws/game/${roomCode}/?token=${playerToken}&name=${encodedName}`
    );

    ws.onopen = () => {
      console.log(`Connected to room ${roomCode}.`);
      setError("");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.error) {
        setError(data.error);
        localStorage.removeItem("active_room");
        setRoomCode("");
        setScreen("lobby");
        return;
      }

      if ("paused" in data) setPaused(data.paused);

      if ("disconnected_player" in data) {
        setDisconnectedPlayer(data.disconnected_player);
      }

      if ("disconnect_timeout_expired" in data) {
        setTimeoutExpired(data.disconnect_timeout_expired);
      }

      if ("game_ended" in data) {
        setGameEnded(data.game_ended);
      }

      if (data.room_id) setRoomCode(data.room_id);
      if (data.started !== undefined) {
        setGameStarted(data.started);
      }

      if (data.host) setHost(data.host);

      if (data.piles) setPiles({...data.piles});

      if (data.hand) setHand(data.hand);

      if (data.turn) setCurrentTurn(data.turn);

      if (data.player) setPlayerId(data.player);

      if (data.counts) setCounts({...data.counts});

      if (data.players) {
        setPlayers([...data.players]);

        if (
          data.started &&
          data.player &&
          !data.players.includes(data.player)
        ) {
          setError("The game has already started. You were not selected for this game.");
          setScreen("lobby");
          localStorage.removeItem("active_room");
        }
      }

      if (data.player_names) {
        setPlayerNames({ ...data.player_names });
      }

      if (data.players_playing_again) {
        setPlayersPlayingAgain([...data.players_playing_again]);
      }
      if (data.scores) setScores(data.scores);
      if ("winner" in data) setWinner(data.winner ?? null);
    };

    ws.onclose = () => {
      console.log("Disconnected from room.");
    };

    setSocket(ws);

    return () => {
      ws.close();
    };

  }, [screen, roomCode]);

  function playCard(card){
    if (!socket) return;

    socket.send(
      JSON.stringify({
        action:"play_card",
        card:card
      })
    );
  }

  // function rankValue(rank){
  //   if(rank === "A") return 1;
  //   if(rank === "J") return 11;
  //   if(rank === "Q") return 12;
  //   if(rank === "K") return 13;

  //   return parseInt(rank);

  // }

  function rankValue(rank) {
    const rankMap = { "A": 1, "J": 11, "Q": 12, "K": 13 };
    return rankMap[rank] || parseInt(rank, 10);
  }

  function isPlayable(card){
    const suit = card.slice(-1);
    const rank = card.slice(0,-1);

    const suitMap = {
      H:"hearts",
      S:"spades",
      D:"diamonds",
      C:"clubs"
    };

    const pile = piles[suitMap[suit]];
    const r = rankValue(rank);
    
    if(pile.low === null){
      return r === 7;
    }

    const low = Number(pile.low);
    const high = Number(pile.high);


    if(r === low - 1) return true;
    if(r === high + 1) return true;

    return false;
  }

  const suitOrder = {H:0, S:1, D:2, C:3};
  const sortedHand = [...hand].sort((a,b) => {
    const suitA = suitOrder[a.slice(-1)];
    const suitB = suitOrder[b.slice(-1)];

    if (suitA !== suitB) return suitA - suitB;

    const rankOrder = {
      A:1,J:11,Q:12,K:13
    };

    const rA = rankOrder[a.slice(0,-1)] || parseInt(a.slice(0,-1));
    const rB = rankOrder[b.slice(0,-1)] || parseInt(b.slice(0,-1));

    return rA - rB;

  });
  
  const hasMove = sortedHand.some(card => isPlayable(card));
  const otherPlayers = players.filter(
    (player) => player !== playerId
  );

  const myIndex = players.indexOf(playerId);

  const playersFromMyPerspective =
    myIndex === -1
      ? players
      : [
          ...players.slice(myIndex),
          ...players.slice(0, myIndex),
        ];

  const opponents = playersFromMyPerspective.slice(1);

  const tablePlayerPositions = opponents.map((player, index) => {
    const opponentCount = opponents.length;

    let angle;

    if (opponentCount === 1) {
      angle = 270;
    } else {
      angle =
        210 +
        (120 * index) / (opponentCount - 1);
    }

    const radians = (angle * Math.PI) / 180;

    const radiusX = 42;
    const radiusY = 55;

    return {
      player,
      left: 50 + radiusX * Math.cos(radians),
      top: 50 + radiusY * Math.sin(radians),
    };
  });


  if (screen === "lobby") {
    return (
      <>
        <Notification
          message={error}
          onClose={() => setError("")}
        />

        {showRules && (
          <HowToPlay onClose={() => setShowRules(false)} />
        )}

        <div className="main-lobby">
          <div className="main-lobby-card">

            <div className="lobby-brand">
              <div className="lobby-suit">♥</div>
              <h1>Sevens</h1>
              <p>Multiplayer Card Game</p>
            </div>

            <div className="name-section">
              <label htmlFor="display-name">
                Display Name
              </label>

              <input
                id="display-name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your name"
                maxLength={20}
              />
            </div>

            <button
              className="primary-lobby-button"
              onClick={createRoom}
              disabled={!displayName.trim()}
            >
              Create Room
            </button>

            <div className="lobby-divider">
              <span>OR</span>
            </div>

            <div className="join-section">
              <label htmlFor="room-code">
                Join an Existing Room
              </label>

              <div className="join-room-row">
                <input
                  id="room-code"
                  type="text"
                  value={roomInput}
                  onChange={(e) =>
                    setRoomInput(e.target.value.toUpperCase())
                  }
                  placeholder="Enter room code"
                  maxLength={6}
                />

                <button
                  className="secondary-lobby-button"
                  onClick={joinRoom}
                  disabled={!displayName.trim() || !roomInput.trim()}
                >
                  Join
                </button>
              </div>
            </div>

            <div className="lobby-info">
              <span>2-6 players</span>
              <span>•</span>
              <span>Play in real time</span>
            </div>

            <button
              className="how-to-play-link"
              onClick={() => setShowRules(true)}
            >
              <span className="info-icon">i</span>
              How to Play
            </button>

          </div>
        </div>
      </>
    );
  }

  return (
    <>
    <Notification
      message={error}
      onClose={() => setError("")}
    />

    {showRules && (
      <HowToPlay onClose={() => setShowRules(false)} />
    )}
      <div className="table-layout">

        {/* =====================================================
            HEADER / ROOM INFORMATION
            ===================================================== */}

        <header className="game-header">

          <div className="game-title-row">

            <div className="game-brand-mark">
              <span className="game-brand-suit">♥</span>

              <div className="game-brand-text">
                <span className="game-brand-title">Sevens</span>
                <span className="game-brand-subtitle">
                  CARD GAME
                </span>
              </div>
            </div>

            <button
              className="rules-info-button"
              onClick={() => setShowRules(true)}
              aria-label="How to Play"
              title="How to Play"
            >
              i
            </button>

          </div>

          <div className="room-info">

            <div className="room-meta">
              <span className="room-meta-label">ROOM</span>
              <span className="room-meta-value">{roomCode}</span>
            </div>

            <div className="room-meta">
              <span className="room-meta-label">HOST</span>
              <span className="room-meta-value">
                {getDisplayName(host)}
              </span>
            </div>

          </div>

        </header>


        {/* =====================================================
            GAME / ROOM STATUS
            ===================================================== */}

        {!gameStarted && !gameEnded && !winner && (
          <div className="room-lobby-overlay">
            <div className="room-lobby-card">

              <div className="room-lobby-brand">
                <div className="room-lobby-suit">♥</div>
                <h2>Game Lobby</h2>
                <p>Waiting for players to join</p>
              </div>

              <div className="room-code-section">
                <span className="room-code-label">ROOM CODE</span>

                <div className="room-code-row">
                  <span className="room-code-value">
                    {roomCode}
                  </span>

                  <button
                    className="copy-room-button"
                    onClick={copyRoomCode}
                  >
                    Copy
                  </button>
                </div>

                <span className="room-code-hint">
                  Share this code with your friends
                </span>
              </div>

              <div className="room-lobby-section">

                <div className="room-lobby-section-header">
                  <h3>Players</h3>
                  <span>{players.length} / 6</span>
                </div>

                <div className="room-player-list">

                  {players.map((player) => (
                    <div
                      key={player}
                      className={
                        player === playerId
                          ? "room-player current"
                          : "room-player"
                      }
                    >

                      <div className="room-player-left">

                        <div className="room-player-avatar">
                          {getDisplayName(player).charAt(0).toUpperCase()}
                        </div>

                        <span className="room-player-name">
                          {getDisplayName(player)}
                        </span>

                      </div>

                      <div className="room-player-right">

                        {player === host && (
                          <span className="host-badge">
                            HOST
                          </span>
                        )}

                        {player === playerId && (
                          <span className="you-badge">
                            YOU
                          </span>
                        )}

                      </div>

                    </div>
                  ))}

                  {Array.from({
                    length: Math.max(0, 6 - players.length)
                  }).map((_, index) => (
                    <div
                      key={`empty-${index}`}
                      className="room-player empty"
                    >
                      <div className="room-player-left">

                        <div className="room-player-avatar empty-avatar">
                          +
                        </div>

                        <span className="room-player-name empty-name">
                          Waiting for player...
                        </span>

                      </div>
                    </div>
                  ))}

                </div>

              </div>

              <div className="room-lobby-status">

                {players.length < 2 ? (
                  <>
                    <div className="status-dot waiting"></div>
                    <span>Waiting for another player</span>
                  </>
                ) : playerId === host ? (
                  <>
                    <div className="status-dot ready"></div>
                    <span>You're ready to start</span>
                  </>
                ) : (
                  <>
                    <div className="status-dot waiting"></div>
                    <span>Waiting for the host to start</span>
                  </>
                )}

              </div>

              <button
                className="room-how-to-play"
                onClick={() => setShowRules(true)}
              >
                How to Play
              </button>

              <div className="room-lobby-actions">

                {playerId === host && players.length >= 2 && (
                  <button
                    className="primary-lobby-button"
                    onClick={startGame}
                  >
                    Start Game
                  </button>
                )}

                <button
                  className="secondary-lobby-button leave-room-button"
                  onClick={leaveGame}
                >
                  Leave Room
                </button>

              </div>

            </div>
          </div>
        )}


        {/* =====================================================
            PAUSED GAME
            ===================================================== */}

        {paused && (
          <div className="pause-overlay">
            <div className="pause-card">

              <div className="pause-icon">
                ⏸
              </div>

              <h2>Game Paused</h2>

              <p className="pause-message">
                {getDisplayName(disconnectedPlayer)} has disconnected.
              </p>

              {!timeoutExpired ? (
                <p className="pause-status">
                  Waiting for reconnection...
                </p>
              ) : (
                <>
                  <p className="pause-status">
                    {getDisplayName(disconnectedPlayer)}
                    {" "}did not reconnect in time.
                  </p>

                  {playerId === host && (
                    <button
                      className="pause-end-button"
                      onClick={endGame}
                    >
                      End Game
                    </button>
                  )}

                  {playerId !== host && (
                    <p className="pause-status">
                      Waiting for the host to end the game.
                    </p>
                  )}
                </>
              )}

            </div>
          </div>
        )}


        {/* =====================================================
            GAME ENDED
            ===================================================== */}

        {gameEnded && (
          <div className="game-ended-overlay">

            <div className="game-ended-card">

              <h2>Game Over</h2>

              {winner && (
                <p>
                  {getDisplayName(winner)} won the game!
                </p>
              )}

              <div className="scores">

                <p className="result-subtitle">
                  Final Scores
                </p>
                <hr></hr>

                {Object.entries(scores).map(
                  ([player, score]) => (
                    <p key={player}>
                      {getDisplayName(player)}: {score}
                    </p>
                  )
                )}

              </div>


              {/* ---------------------------------------------
                  REMATCH STATUS
                  --------------------------------------------- */}

              <div className="rematch-status">

                <p>
                  {playersPlayingAgain.length} / {players.length}
                  {" "}players ready for another game
                </p>

                {players.map((player) => (
                  <p key={player}>
                    {getDisplayName(player)}
                    {" "}
                    {playersPlayingAgain.includes(player)
                      ? ": Ready"
                      : ": Waiting"}
                  </p>
                ))}

              </div>


              {/* ---------------------------------------------
                  PLAY AGAIN
                  --------------------------------------------- */}

              <div className="result-actions">

              {!playersPlayingAgain.includes(playerId) && (
                <button
                  className="result-primary-button"
                  onClick={rematch}
                >
                  Play Again
                </button>
              )}

              {playerId === host && (
                <button
                  className="result-primary-button"
                  onClick={startGame}
                  disabled={playersPlayingAgain.length < 2}
                >
                  Start Game
                </button>
              )}

              <button
                className="result-secondary-button"
                onClick={leaveGame}
              >
                Leave Room
              </button>

            </div>

            {playersPlayingAgain.includes(playerId) && (
              <p>
                You are ready for the next game.
              </p>
            )}

            </div>

          </div>
        )}


        {/* =====================================================
            NORMAL WINNER
            ===================================================== */}

        {winner && !gameEnded && (
          <div className="winner-overlay">

            <div className="winner-box">

              <div className="result-suit">♥</div>

                <h2>{getDisplayName(winner)} wins!</h2>


              <hr />

              <div className="score-list">

                <p className="result-subtitle">
                  Final Scores:
                </p>

                {Object.entries(scores).map(
                  ([pId, score]) => (
                    <p
                      key={pId}
                      className={
                        pId === winner
                          ? "winner-score"
                          : "normal-score"
                      }
                    >
                      {getDisplayName(pId)}:
                      <strong>{score}</strong>
                    </p>
                  )
                )}

              </div>


              {/* ---------------------------------------------
                  REMATCH STATUS
                  --------------------------------------------- */}

              <div className="rematch-status">

                <p>
                  {playersPlayingAgain.length} / {players.length}
                  {" "}players ready for another game
                </p>

                {players.map((player) => (
                  <p key={player}>
                    {getDisplayName(player)}
                    {" "}
                    {playersPlayingAgain.includes(player)
                      ? ": Ready"
                      : ": Waiting"}
                  </p>
                ))}

              </div>


              <div className="result-actions">

                {!playersPlayingAgain.includes(playerId) && (
                  <button
                    className="result-primary-button"
                    onClick={rematch}
                  >
                    Play Again
                  </button>
                )}

                {playerId === host && (
                  <button
                    className="result-primary-button"
                    onClick={startGame}
                    disabled={playersPlayingAgain.length < 2}
                  >
                    Start Game
                  </button>
                )}

                <button
                  className="result-secondary-button"
                  onClick={leaveGame}
                >
                  Leave Room
                </button>

              </div>

              {playersPlayingAgain.includes(playerId) && (
                <p>
                  You are ready for the next game.
                </p>
              )}

            </div>

          </div>
        )}


        {/* =====================================================
            PLAYERS / TABLE
            ===================================================== */}

        {gameStarted && (
  <div className="game-board">

      <div className="table-stage">

        <div className="players-area">
          {tablePlayerPositions.map(({ player, left, top }) => (
            <div
              key={player}
              className="table-player"
              style={{
                left: `${left}%`,
                top: `${top}%`,
              }}
            >
              <div
                className={
                  currentTurn === player
                    ? "table-player-card active"
                    : "table-player-card"
                }
              >
                <span className="table-player-name">
                  {getDisplayName(player)}
                </span>

                <span className="table-player-count">
                  {counts[player] || 0} cards
                </span>
              </div>
            </div>
          ))}
        </div>

        <div
          className={
            currentTurn === playerId
              ? "current-turn-indicator my-turn"
              : "current-turn-indicator"
          }
        >
          {currentTurn === playerId
            ? "Your turn"
            : `${getDisplayName(currentTurn)}'s turn`}
        </div>

        <div className="table-wrapper">
          <Table piles={piles} />
        </div>

      </div>

      <div
        className={
          currentTurn === playerId
            ? "your-area active"
            : "your-area"
        }
      >
        <div className="your-player-name">
          {getDisplayName(playerId)}

          <span>
            {counts[playerId] || 0}
          </span>
        </div>

        <Hand
          cards={sortedHand}
          playCard={playCard}
          isMyTurn={isMyTurn}
          isPlayable={isPlayable}
        />

        <button
          className="pass-button"
          onClick={passTurn}
          disabled={!isMyTurn || hasMove}
        >
          Pass
        </button>
      </div>


    </div>
  )}

      </div>
    </>
  );
}
export default App;
