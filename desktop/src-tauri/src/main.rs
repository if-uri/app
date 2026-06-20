// Author: Tom Sapletta · https://tom.sapletta.com
// Part of the ifURI solution.

// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
  ifuri_voice_lib::run();
}
