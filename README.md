# Multiplayer Sevens Card Game

A **real-time multiplayer implementation of the classic card game "Sevens"** built with **Django, WebSockets, and React**.

Players can connect from multiple devices on the same network and play interactively with synchronized game state.

---

## Features

- Real-time multiplayer gameplay using **WebSockets**
- **4-player card game engine**
- Turn-based system with rule validation
- **Pass turn** functionality, which is enabled only when you are out of moves
- Highlighting of **valid playable cards**
- Responsive UI that works on **desktop and mobile**
- Visual card display using SVG cards
- Dynamic table layout showing players around the table
- Local multiplayer over WiFi
- Winner display with points of each player once game ends
- Play again option without restarting the server

---

## Tech Stack

### Backend
- Django
- Django Channels
- WebSockets (ASGI / Daphne)

### Frontend
- React
- JavaScript
- CSS

### Networking
- Local multiplayer over WiFi

---

## Game Rules (Sevens)

- The player with **7 of Hearts starts the game**
- Cards are placed in ascending and descending order from 7

Example pile progression:

```
A 2 3 4 5 6 7 8 9 10 J Q K
```

- If a player cannot play a card, they must **pass**
- The first player to play all cards **wins**

---

## How to Run the Project

### 1. Clone the Repository

---

### 2. Start the Backend
Open a new terminal:
```
cd backend/cardgame
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

---

### 3. Start the React Frontend
In another terminal:
```
cd frontend/cardgame-ui
npm install
npm start
```

---

### 4. Connect Multiple Players

Open the game from multiple devices using:

```
http://<YOUR_IP_ADDRESS>:3000
```

All devices must be connected to the **same WiFi network**.

---

## Future Improvements

Planned enhancements:

- Fan-style card display for a more realistic hand
- Card animations when playing to the table
- Persistent game rooms
- Online multiplayer (not limited to LAN)
- Player avatars
- Score tracking across rounds

---

## Learning Outcomes

This project demonstrates:

- Real-time systems using **WebSockets**
- Backend architecture with **Django Channels**
- Multiplayer state synchronization
- React component-based UI design
- Networking concepts for local multiplayer

---

## Author

**Salaj Bansal**
