package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"
)

func TestSyncRoomIsIdempotentAndPersistent(t *testing.T) {
	statePath := filepath.Join(t.TempDir(), "rooms.json")
	store, err := newRoomStore(statePath)
	if err != nil {
		t.Fatal(err)
	}
	server := newHandler(store)
	payload := `{"room_id":2,"status":"active","hint_unlocked":1}`

	for attempt := 0; attempt < 2; attempt++ {
		request := httptest.NewRequest(http.MethodPost, "/api/v1/sync", strings.NewReader(payload))
		response := httptest.NewRecorder()
		server.ServeHTTP(response, request)
		if response.Code != http.StatusAccepted {
			t.Fatalf("sync returned %d: %s", response.Code, response.Body.String())
		}
	}

	reloaded, err := newRoomStore(statePath)
	if err != nil {
		t.Fatal(err)
	}
	request := httptest.NewRequest(http.MethodGet, "/api/v1/rooms", nil)
	response := httptest.NewRecorder()
	newHandler(reloaded).ServeHTTP(response, request)
	if response.Code != http.StatusOK {
		t.Fatalf("list returned %d", response.Code)
	}
	var rooms []Room
	if err := json.Unmarshal(response.Body.Bytes(), &rooms); err != nil {
		t.Fatal(err)
	}
	if len(rooms) != 1 || rooms[0] != (Room{RoomID: 2, Status: "active", HintUnlocked: 1}) {
		t.Fatalf("unexpected persisted rooms: %+v", rooms)
	}
}

func TestSyncRoomRejectsInvalidPayloads(t *testing.T) {
	store, err := newRoomStore("")
	if err != nil {
		t.Fatal(err)
	}
	for _, payload := range []string{
		`{"room_id":0,"status":"locked","hint_unlocked":0}`,
		`{"room_id":1,"status":"unknown","hint_unlocked":0}`,
		`{"room_id":1,"status":"locked","hint_unlocked":2}`,
		`{"room_id":1,"status":"locked"}`,
		`{"room_id":1,"status":"locked","hint_unlocked":0,"extra":true}`,
	} {
		request := httptest.NewRequest(http.MethodPost, "/api/v1/sync", strings.NewReader(payload))
		response := httptest.NewRecorder()
		newHandler(store).ServeHTTP(response, request)
		if response.Code != http.StatusBadRequest {
			t.Errorf("payload %s returned %d, want %d", payload, response.Code, http.StatusBadRequest)
		}
	}
}
