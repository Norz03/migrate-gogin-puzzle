package main

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"sync"
)

type roomStore struct {
	mu        sync.RWMutex
	rooms     map[int]Room
	statePath string
}

func newRoomStore(statePath string) (*roomStore, error) {
	store := &roomStore{rooms: make(map[int]Room), statePath: statePath}
	if statePath == "" {
		return store, nil
	}

	data, err := os.ReadFile(statePath)
	if errors.Is(err, os.ErrNotExist) {
		return store, nil
	}
	if err != nil {
		return nil, err
	}
	var rooms []Room
	if err := json.Unmarshal(data, &rooms); err != nil {
		return nil, err
	}
	for _, room := range rooms {
		if err := validateRoom(room); err != nil {
			return nil, err
		}
		if _, exists := store.rooms[room.RoomID]; exists {
			return nil, errors.New("state file contains duplicate room IDs")
		}
		store.rooms[room.RoomID] = room
	}
	return store, nil
}

func (s *roomStore) upsert(room Room) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	updated := make(map[int]Room, len(s.rooms)+1)
	for roomID, existing := range s.rooms {
		updated[roomID] = existing
	}
	updated[room.RoomID] = room
	if s.statePath != "" {
		if err := persistRooms(s.statePath, updated); err != nil {
			return err
		}
	}
	s.rooms = updated
	return nil
}

func persistRooms(statePath string, rooms map[int]Room) error {
	ordered := make([]Room, 0, len(rooms))
	for _, room := range rooms {
		ordered = append(ordered, room)
	}
	sort.Slice(ordered, func(i, j int) bool {
		return ordered[i].RoomID < ordered[j].RoomID
	})
	if err := os.MkdirAll(filepath.Dir(statePath), 0755); err != nil {
		return err
	}
	temporaryFile, err := os.CreateTemp(filepath.Dir(statePath), ".rooms-*.json")
	if err != nil {
		return err
	}
	defer os.Remove(temporaryFile.Name())
	if err := json.NewEncoder(temporaryFile).Encode(ordered); err != nil {
		temporaryFile.Close()
		return err
	}
	if err := temporaryFile.Close(); err != nil {
		return err
	}
	return os.Rename(temporaryFile.Name(), statePath)
}

func validateRoom(room Room) error {
	if room.RoomID <= 0 {
		return errors.New("room_id must be a positive integer")
	}
	if room.Status != "locked" && room.Status != "active" && room.Status != "cleared" {
		return errors.New("status must be locked, active, or cleared")
	}
	if room.HintUnlocked != 0 && room.HintUnlocked != 1 {
		return errors.New("hint_unlocked must be 0 or 1")
	}
	return nil
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}

func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *roomStore) syncRoomHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	var request roomRequest
	if err := decoder.Decode(&request); err != nil {
		http.Error(w, "invalid JSON payload", http.StatusBadRequest)
		return
	}
	if err := decoder.Decode(&struct{}{}); err != io.EOF {
		http.Error(w, "request must contain one JSON object", http.StatusBadRequest)
		return
	}
	if request.RoomID == nil || request.Status == nil || request.HintUnlocked == nil {
		http.Error(w, "room_id, status, and hint_unlocked are required", http.StatusBadRequest)
		return
	}
	room := Room{
		RoomID:       *request.RoomID,
		Status:       *request.Status,
		HintUnlocked: *request.HintUnlocked,
	}
	if err := validateRoom(room); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if err := s.upsert(room); err != nil {
		http.Error(w, "could not persist room state", http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusAccepted, room)
}

func (s *roomStore) listRoomsHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.mu.RLock()
	rooms := make([]Room, 0, len(s.rooms))
	for _, room := range s.rooms {
		rooms = append(rooms, room)
	}
	s.mu.RUnlock()
	sort.Slice(rooms, func(i, j int) bool {
		return rooms[i].RoomID < rooms[j].RoomID
	})
	writeJSON(w, http.StatusOK, rooms)
}
