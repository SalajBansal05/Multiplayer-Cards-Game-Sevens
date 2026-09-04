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
  
  const [hand, setHand] = useState([]);
  
  const [currentTurn, setCurrentTurn] = useState(null);
  
  const [playerId, setPlayerId] = useState(null);
  
  const isMyTurn = playerId === currentTurn;

  const [counts, setCounts] = useState({});

  const [players, setPlayers] = useState([]);

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

  function passTurn(){
    if (!socket) return;
  
    socket.send(
      JSON.stringify({
        action: "pass"
      })
    );
  
  }

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
      if (data.room_id) setRoomCode(data.room_id);
      if (data.started !== undefined) setGameStarted(data.started);
      if (data.host) setHost(data.host);
      if (data.piles) setPiles({...data.piles});
      if (data.hand) setHand(data.hand);
      if (data.turn) setCurrentTurn(data.turn);
      if (data.player) setPlayerId(data.player);
      if (data.counts) setCounts({...data.counts});
      if (data.players) setPlayers([...data.players]);
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

  let topPlayer = null;
  let leftPlayer = null;
  let rightPlayer = null;

  if (players.length === 4 && playerId) {

    const i = players.indexOf(playerId);

    topPlayer = players[(i + 2) % 4];
    leftPlayer = players[(i + 3) % 4];
    rightPlayer = players[(i + 1) % 4];

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
        <h1>Card Game - Sevens</h1>
        {winner && (
          <div className="winner-overlay">
            <div className="winner-box">
              <h2>{winner} wins!</h2>
              <hr />
              <div className="score-list">
                <h3>Final Scores:</h3>
                {Object.entries(scores).map(([pId, score]) => (
                  <p key={pId} style={{ color: pId === winner ? 'green' : 'black' }}>
                    {pId}: <strong>{score}</strong>
                  </p>
                ))}
              </div>
              <button onClick={rematch} style={{ marginTop: '20px' }}>Play Again</button>
            </div>
          </div>
        )}
        <div>
          <strong>Room Code:</strong> {roomCode}
        </div>

        <div>
          <strong>Host:</strong> {host}
        </div>

        <div>
          <strong>You are:</strong> {playerId}
        </div>

        {!gameStarted && (
          <div>
            <h2>Waiting for players</h2>
            <p>
              {players.length} / 4 players connected
            </p>
          </div>
        )}
        {(!gameStarted || winner) && (
          <button onClick={leaveGame}>
            Leave Game
          </button>
        )}

        <div className={currentTurn === topPlayer ? "player top active" : "player top"}>
          {topPlayer} ({counts[topPlayer] || 0})
        </div>

        <div className="middle-row">

          <div className={currentTurn === leftPlayer ? "player left active" : "player left"}>
            {leftPlayer} ({counts[leftPlayer] || 0})
          </div>

          <div className="table-center">
            <Table piles={piles} />
          </div>

          <div className={currentTurn === rightPlayer ? "player right active" : "player right"}>
            {rightPlayer} ({counts[rightPlayer] || 0})
          </div>

        </div>

        <div className={currentTurn === playerId ? "player bottom active" : "player bottom"}>

          <h3>You ({counts[playerId] || 0})</h3>

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

        <h3>Current Turn: {currentTurn}</h3>

      </div>
      <div className="rules">
        <h2>Rules:</h2>
        <p>1. The player who has the 7 of hearts starts first. <br/> </p>
        <p>2. The chance moves in cyclic order and each player has to add a card to any pile, either the next higher card of a suit or the next lower one. <br/> </p>
        <p>3. If no such move is possible, players shall pass. <br/> </p>
        <p>4. Game is over when a player's hand becomes empty. <br/> </p>
        <p>5. Score is calculated as the sum of the values of the cards in each player's hand. <br/> </p>
        <p>6. The player with least score wins. <br/> </p>
      </div>
    </>
  );
}

export default App;
