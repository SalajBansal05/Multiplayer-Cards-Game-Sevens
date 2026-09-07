import './App.css';
import {useEffect, useState} from "react"
import Hand from './components/Hand';
import Table from './components/Table';

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

  const [screen, setScreen] = useState("lobby");
  const [roomCode, setRoomCode] = useState("");
  const [roomInput, setRoomInput] = useState("");
  const [error, setError] = useState("");
  const [gameStarted, setGameStarted] = useState(false);
  const [host, setHost] = useState(null);

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
    const savedRoom = localStorage.getItem("active_room");

    if (savedRoom) {
      setRoomCode(savedRoom);
      setScreen("game");
    }
  }, []);

  useEffect(() => {
    if (screen !== "game" || !roomCode) {
      return;
    }

    const playerToken = getPlayerToken();

    const ws = new WebSocket(
      `ws://${window.location.hostname}:8000/ws/game/${roomCode}/?token=${playerToken}`
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

  if (screen === "lobby") {
    return (
      <div className="lobby">
        <h1>Card Game - Sevens</h1>

        <button onClick={createRoom}>
          Create Game
        </button>

        <div>
          <input
            type="text"
            value={roomInput}
            onChange={(e) => setRoomInput(e.target.value)}
            placeholder="Room Code"
            maxLength={6}
          />

          <button onClick={joinRoom}>
            Join Game
          </button>
        </div>

        {error && (
          <p>{error}</p>
        )}
      </div>
    );
  }

  return (
    <>
      <div className="table-layout">

        {/* =====================================================
            HEADER / ROOM INFORMATION
            ===================================================== */}

        <header className="game-header">
          <h1>Card Game - Sevens</h1>

          <div className="room-info">
            <p>
              <strong>Room Code:</strong> {roomCode}
            </p>

            <p>
              <strong>Host:</strong> {host}
            </p>

            <p>
              <strong>You are:</strong> {playerId}
            </p>
          </div>
        </header>


        {/* =====================================================
            GAME / ROOM STATUS
            ===================================================== */}

        {!gameStarted && !gameEnded && !winner && (
          <div className="game-status">

            <h2>Waiting for host to start the game</h2>

            <p>
              {players.length} / 6 players in room
            </p>

            {players.length < 2 && (
              <p>
                At least 2 players are required to start.
              </p>
            )}

            {players.length >= 2 && playerId !== host && (
              <p>
                Waiting for the host to start the game...
              </p>
            )}

            <div className="lobby-buttons">

              {playerId === host && players.length >= 2 && (
                <button onClick={startGame}>
                  Start Game
                </button>
              )}

              <button onClick={leaveGame}>
                Leave Game
              </button>

            </div>

          </div>
        )}


        {/* =====================================================
            PAUSED GAME
            ===================================================== */}

        {paused && (
          <div className="game-status">

            <h2>Game Paused</h2>

            <p>
              {disconnectedPlayer} has disconnected.
            </p>

            {!timeoutExpired && (
              <p>
                Waiting for reconnection...
              </p>
            )}

            {timeoutExpired && (
              <p>
                {disconnectedPlayer} did not reconnect in time.
              </p>
            )}

          </div>
        )}


        {paused && timeoutExpired && playerId === host && (
          <div className="game-status">

            <button onClick={endGame}>
              End Game
            </button>

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
                  {winner} won the game!
                </p>
              )}

              <div className="scores">

                {Object.entries(scores).map(
                  ([player, score]) => (
                    <p key={player}>
                      {player}: {score}
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
                    {player}
                    {" "}
                    {playersPlayingAgain.includes(player)
                      ? "✓ Ready"
                      : "Waiting"}
                  </p>
                ))}

              </div>


              {/* ---------------------------------------------
                  PLAY AGAIN
                  --------------------------------------------- */}

              {!playersPlayingAgain.includes(playerId) ? (
                <button onClick={rematch}>
                  Play Again
                </button>
              ) : (
                <p>
                  You are ready for the next game.
                </p>
              )}


              {/* ---------------------------------------------
                  HOST START
                  --------------------------------------------- */}

              {playerId === host && (
                <button
                  onClick={startGame}
                  disabled={playersPlayingAgain.length < 2}
                >
                  Start Game
                </button>
              )}


              <button onClick={leaveGame}>
                Leave Room
              </button>

            </div>

          </div>
        )}


        {/* =====================================================
            NORMAL WINNER
            ===================================================== */}

        {winner && !gameEnded && (
          <div className="winner-overlay">

            <div className="winner-box">

              <h2>{winner} wins!</h2>

              <hr />

              <div className="score-list">

                <h3>Final Scores:</h3>

                {Object.entries(scores).map(
                  ([pId, score]) => (
                    <p
                      key={pId}
                      style={{
                        color:
                          pId === winner
                            ? "green"
                            : "black"
                      }}
                    >
                      {pId}: <strong>{score}</strong>
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
                    {player}
                    {" "}
                    {playersPlayingAgain.includes(player)
                      ? "✓ Ready"
                      : "Waiting"}
                  </p>
                ))}

              </div>


              {!playersPlayingAgain.includes(playerId) ? (
                <button
                  onClick={rematch}
                  style={{ marginTop: "20px" }}
                >
                  Play Again
                </button>
              ) : (
                <p>
                  You are ready for the next game.
                </p>
              )}


              {playerId === host && (
                <button
                  onClick={startGame}
                  disabled={playersPlayingAgain.length < 2}
                  style={{ marginTop: "10px" }}
                >
                  Start Game
                </button>
              )}


              {!timeoutExpired && (
                <button
                  onClick={leaveGame}
                  style={{ marginTop: "10px" }}
                >
                  Leave Game
                </button>
              )}

            </div>

          </div>
        )}


        {/* =====================================================
            PLAYERS / TABLE
            ===================================================== */}

        {gameStarted && (
          <div className="players-area">

            <h2>Players</h2>

            <div className="players-list">

              {players
                .filter((player) => player !== playerId)
                .map((player) => (
                  <div
                    key={player}
                    className={
                      currentTurn === player
                        ? "player active"
                        : "player"
                    }
                  >
                    <span className="player-name">
                      {player}
                    </span>

                    <span className="player-card-count">
                      {counts[player] || 0} cards
                    </span>
                  </div>
                ))}

            </div>


            <div className="table-center">

              <Table piles={piles} />

            </div>

          </div>
        )}


        {/* =====================================================
            YOUR HAND / ACTIONS
            ===================================================== */}

        {gameStarted && (
          <div
            className={
              currentTurn === playerId
                ? "player bottom active"
                : "player bottom"
            }
          >

            <h3>
              You ({counts[playerId] || 0})
            </h3>

            <Hand
              cards={sortedHand}
              playCard={playCard}
              isMyTurn={isMyTurn}
              isPlayable={isPlayable}
            />

            <button
              onClick={passTurn}
              disabled={!isMyTurn || hasMove}
            >
              Pass
            </button>

          </div>
        )}


        {gameStarted && (
          <h3>
            Current Turn: {currentTurn}
          </h3>
        )}


        {/* =====================================================
            LEAVE GAME
            ===================================================== */}

        

      </div>


      {/* =========================================================
          RULES
          ========================================================= */}

      <div className="rules">

        <h2>Rules:</h2>

        <p>
          1. The player who has the 7 of hearts starts first.
        </p>

        <p>
          2. The chance moves in cyclic order and each player
          has to add a card to any pile, either the next higher
          card of a suit or the next lower one.
        </p>

        <p>
          3. If no such move is possible, players shall pass.
        </p>

        <p>
          4. Game is over when a player's hand becomes empty.
        </p>

        <p>
          5. Score is calculated as the sum of the values of
          the cards in each player's hand.
        </p>

        <p>
          6. The player with least score wins.
        </p>

      </div>
    </>
  );
}
export default App;
