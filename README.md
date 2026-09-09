# Multiplayer Sevens Card Game

A **real-time multiplayer implementation of the classic card game Sevens**, built with **Django, Django Channels, WebSockets, and React**.

Players can create or join game rooms, connect from multiple devices on the same local network, and play with synchronized game state in real time.

---

## Features

- Real-time multiplayer gameplay using **WebSockets**
- Support for **2–6 players per room**
- Rule-validated turn-based gameplay
- **7 of Hearts** is required as the first card
- **Pass** is available only when the current player has no legal move
- Playable cards are visually highlighted
- Persistent player identity using a browser-stored player token
- Automatic reconnection support for temporary disconnections
- Disconnect timeout handling for the current player
- Host reassignment when the host leaves or times out
- Host-controlled game starts
- Room lobby with player list, host indicator, and room code sharing
- Rematch system where players explicitly choose **Play Again**
- Rematches preserve the existing player order and include only opted-in players
- Dynamic player layout around the table for 2–6 players
- Responsive interface for desktop and mobile screens
- In-game **How to Play** modal
- Toast-style notifications for user feedback
- Winner and final-score displays
- Host-controlled game termination after a disconnect timeout
- Leave-room functionality
- Card visuals using SVG assets
- Local multiplayer over Wi-Fi

---

## Tech Stack

### Backend

- **Django**
- **Django Channels**
- **WebSockets**
- **ASGI / Daphne**

### Frontend

- **React**
- **JavaScript**
- **CSS**

### Networking

- Local multiplayer over a shared Wi-Fi network
- WebSocket-based synchronization between clients

---

## Game Rules

Sevens is played with a standard 52-card deck.

1. The player holding the **7 of Hearts** starts the game.
2. Each suit begins from its 7.
3. Once a suit has started, cards can be added only to the next higher or next lower rank.
4. If a player has no legal move, they must **pass**.
5. Turns proceed in cyclic order through the active players.
6. The game ends when a player's hand becomes empty.
7. The final score of a player is the sum of the values of the cards remaining in their hand.
8. The player with the lowest remaining score wins.

Example suit progression:

```text
A 2 3 4 5 6 7 8 9 10 J Q K
          <- ->
```

---

## Multiplayer Rooms

The application uses an in-memory room manager to maintain separate game rooms.

A room has:

- A unique room code
- A host
- A `GameManager` containing the current game state
- 2–6 players
- Player connection and identity information

The host controls when a game starts. Players can join the room while it is waiting for a game to begin.

After a game ends, players can independently choose **Play Again**. The host can start the next game once at least two players have opted in. Players who do not opt in are not included in that rematch.

Room and game state are **in memory**, so restarting the backend server clears active rooms and games.

---

## Disconnect and Reconnection Handling

The game handles temporary player disconnections during an active game.

- If the disconnected player is **not** the current player, the game can continue.
- If the disconnected player is the current player, the game is paused.
- The player has a limited reconnection window to return using their stored player token.
- If they do not reconnect before the timeout, the player is removed from the active match.
- If the disconnected player was the host, a remaining player becomes the new host.
- The game remains paused after a timeout until the host explicitly ends it.

This keeps a required player's disappearance from silently changing the state of the game.

---

## Project Structure

```text
CardGame_Sevens/
├── backend/
│   └── cardgame/
│       ├── cardgame/
│       ├── game/
│       ├── manage.py
│       └── requirements.txt
│
└── frontend/
    └── cardgame-ui/
        ├── src/
        │   ├── components/
        │   ├── App.js
        │   └── App.css
        └── package.json
```

---

## How to Run the Project

### 1. Clone the Repository

```bash
git clone https://github.com/SalajBansal05/Multiplayer-Cards-Game-Sevens.git
cd Multiplayer-Cards-Game-Sevens
```

### 2. Start the Backend

Open a terminal:

```bash
cd backend/cardgame
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

### 3. Start the React Frontend

Open another terminal:

```bash
cd frontend/cardgame-ui
npm install
npm start
```

### 4. Connect Multiple Players

On the host machine, find its local IP address and open:

```text
http://<YOUR_IP_ADDRESS>:3000
```
The IP address using which other can access is provided when you run npm start in terminal.

Open the same address on other devices connected to the **same Wi-Fi network**.

Players can then create a room or join an existing room using its six-character room code.

---

## Development and Testing

The backend contains automated tests covering the game engine, player identity, rooms, connection handling, player limits, host behavior, game lifecycle, and rematches.

Run the Django test suite with:

```bash
cd backend/cardgame
python manage.py test
```

The frontend can be checked with:

```bash
cd frontend/cardgame-ui
npm run build
```

---

## Commit History

The project was developed incrementally so that each major feature could be introduced and tested separately.

### Commit 1 — Stabilize Game Rules and State

- Enforced the **7 of Hearts** first-play rule.
- Added connection-state tracking.
- Added handling for disconnected players.
- Added tests for the core game-state behavior.

### Commit 2 — Persistent Player Identity and Reconnection

- Added persistent browser-stored player tokens.
- Allowed a reconnecting browser to recover its existing player identity.
- Passed player tokens through the WebSocket connection.
- Added reconnection-related tests.

### Commit 3 — Room-Based Multiplayer and Host Lobby

- Replaced the single global game with a **room-based architecture**.
- Added `RoomManager` and per-room `GameManager` instances.
- Added room creation and room-code joining.
- Added host assignment and host reassignment.
- Added room-size restrictions and lobby behavior.
- Added leave-room support.

### Commit 4 — Disconnect Timeout and Game Lifecycle

- Paused the game when the current player disconnected.
- Added a reconnection timeout.
- Removed players who failed to reconnect in time.
- Reassigned the host when necessary.
- Added host-controlled **End Game** behavior after timeout.
- Preserved final scores when the game ends.
- Added tests covering disconnect and game lifecycle behavior.

### Commit 5 — Host-Controlled Starts and Rematches

- Expanded rooms to support **2–6 players**.
- Replaced automatic starts with **host-controlled game starts**.
- Added explicit **Play Again** selection.
- Started rematches using only players who opted in.
- Preserved player order when selecting rematch participants.
- Kept token and connection state consistent across rematches.
- Added lobby and rematch UI.
- Added tests for variable player counts and rematch selection.

### Commit 6 — Refine multiplayer flow, responsive UI, and documentation

- Improved player name handling across multiplayer game state.
- Refined disconnect, host, and rematch state handling.
- Redesigned the lobby and room lobby interfaces.
- Added a responsive casino-style game table and player positioning.
- Improved desktop and mobile layouts.
- Added How to Play and notification components.
- Refined game-state, result, and rematch presentation.
- Cleaned up frontend styling and updated project documentation.

---

## Current Scope

This project is designed as a **local-network multiplayer game** rather than a production online service.

The current implementation intentionally keeps game and room state in memory. A server restart therefore resets all active games and rooms.

---

## Future Improvements

Possible future extensions include:

- Online multiplayer beyond a local Wi-Fi network
- Persistent rooms and games backed by a database
- Animated card movements and transitions
- More sophisticated mobile hand/card presentation
- Persistent score tracking across multiple rounds
- Player avatars beyond the current initials-based presentation

---

## Learning Outcomes

This project demonstrates:

- Real-time application development using **WebSockets**
- Backend architecture using **Django Channels**
- Multiplayer state synchronization
- Room-based game management
- Connection and reconnection handling
- React component-based UI development
- Responsive CSS design
- Local-network client/server communication
- Incremental development through feature-based Git commits

---

## Author

**Salaj Bansal**
