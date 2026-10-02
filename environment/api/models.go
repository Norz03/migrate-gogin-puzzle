package main

// Room represents the state of a Puzzle Tower room.
type Room struct {
	RoomID       int    `json:"room_id"`
	Status       string `json:"status"`
	HintUnlocked int    `json:"hint_unlocked"`
}

type roomRequest struct {
	RoomID       *int    `json:"room_id"`
	Status       *string `json:"status"`
	HintUnlocked *int    `json:"hint_unlocked"`
}
