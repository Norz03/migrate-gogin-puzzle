package main

import (
	"log"
	"net/http"
	"os"
	"time"
)

func newHandler(store *roomStore) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthCheckHandler)
	mux.HandleFunc("/api/v1/sync", store.syncRoomHandler)
	mux.HandleFunc("/api/v1/rooms", store.listRoomsHandler)
	return mux
}

func main() {
	statePath := os.Getenv("TOWER_STATE_PATH")
	if statePath == "" {
		statePath = "../data/rooms.json"
	}
	store, err := newRoomStore(statePath)
	if err != nil {
		log.Fatalf("load API state: %v", err)
	}
	address := os.Getenv("TOWER_API_ADDR")
	if address == "" {
		address = "127.0.0.1:8080"
	}
	server := &http.Server{
		Addr:              address,
		Handler:           newHandler(store),
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Printf("Puzzle Tower API listening on %s", address)
	log.Fatal(server.ListenAndServe())
}
