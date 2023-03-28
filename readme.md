<div align="center">
  <img src="romm.svg" height="128px" width="auto" alt="Gameyfin Logo">
  <h1 style="padding:20px;">RomM (Rom Manager)</h1>
  <br/><br/>
</div>

# Overview

Inspired by [Jellyfin](https://jellyfin.org/) and after found that the awesome [Gameyfin](https://github.com/grimsi/gameyfin) project is not supported for arm64 architectures and it is a general game library manager, I decided to develop my own game library solution, focused on retro gaming.

For now, it is only available as a docker [image](https://hub.docker.com/r/zurdi15/romm) (amd64/arm64)

## ⚡ Features

* Scans your game library (all at once or by platform) and enriches it with IGDB metadata
* Access your library via your web-browser
* Possibility to select one of the matching IGDB results if the scan doesn't get the right one
* Download games directly from your web-browser
* Edit your game files directly from your web-browser
* Works with SQLite or MaridDB (SQLite by default)
* Responsive design
* Light and dark theme

## 🛠 Roadmap

* Set a custom cover for each game
* Upload games directly from your web-browser
* Manage save files directly from your web-browser

# Prerequisites

## ⚠️ Folder structure

To allow RomM scan your retro games library, it should follow the following structure:

```
library/
├─ gbc/
│  ├─ roms/
│     ├─ rom_1.gbc
│     ├─ rom_2.gbc
|
├─ gba/
│  ├─ roms/
│     ├─ rom_1.gba
│     ├─ rom_2.gba
|
├─ gb/
│  ├─ roms/
│     ├─ rom_1.gb
│     ├─ rom_1.gb
```

# Preview

## 🖥 Desktop

https://user-images.githubusercontent.com/34356590/227992371-33056130-c067-49c1-ae32-b3ba78db6798.mp4

## 📱 Mobile

https://user-images.githubusercontent.com/34356590/228007442-0a9cbf6b-4b62-4c1a-aad8-48b13e6337e8.mp4

# Docker image

Last version of the docker [image](https://hub.docker.com/r/zurdi15/romm/tags)

## 🐳 Installation

Check the [docker-compose.yml](https://github.com/zurdi15/romm/blob/master/docker/docker-compose.example.yml) example

Get API key from [IGDB](https://api-docs.igdb.com/#about) for the CLIENT_ID and CLIENT_SECRET variables. 

# Platforms support 

## 🎮 Naming convention

If the RomM folders structure is followed, any kind of platform/folder-name is supported for the core features. For having extra metadata as well as cover images and platforms icons, the following table shows how to name your platforms folders.
This will change over the time, adding games metadata for more platforms. Make sure that the platforms folder names are lowercase.

| slug          | name                                | games metadata |
|---------------|-------------------------------------|----------------|
| 3ds           | Nintendo 3DS                        | ✅             |
| amiga         | Amiga                               | ✅             |
| arcade        | Arcade                              | ✅             |
| atari         | atari                               | ❌             |
| coleco        | coleco                              | ❌             |
| commodore     | commodore                           | ❌             |
| cpc           | cpc                                 | ❌             |
| cps1          | cps1                                | ❌             |
| cps2          | cps2                                | ❌             |
| cps3          | cps3                                | ❌             |
| daphne        | daphne                              | ❌             |
| dc            | Dreamcast                           | ✅             |
| dos           | DOS                                 | ✅             |
| fairchild     | fairchild                           | ❌             |
| fba2012       | fba2012                             | ❌             |
| fbneo         | fbneo                               | ❌             |
| fds           | Family Computer Disk System         | ✅             |
| gb            | Game Boy                            | ✅             |
| gba           | Game Boy Advance                    | ✅             |
| gbc           | Game Boy Color                      | ✅             |
| gg            | gg                                  | ❌             |
| gw            | gw                                  | ❌             |
| intellivision | Intellivision                       | ✅             |
| jaguar        | Atari Jaguar                        | ✅             |
| lynx          | Atari Lynx                          | ✅             |
| md            | md                                  | ❌             |
| megaduck      | megaduck                            | ❌             |
| ms            | ms                                  | ❌             |
| msx           | MSX                                 | ✅             |
| n64           | Nintendo 64                         | ✅             |
| nds           | Nintendo DS                         | ✅             |
| neocd         | neocd                               | ❌             |
| neogeo        | neogeo                              | ❌             |
| nes           | Nintendo Entertainment System       | ✅             |
| ngp           | ngp                                 | ❌             |
| odyssey       | odyssey                             | ❌             |
| pce           | pce                                 | ❌             |
| pcecd         | pcecd                               | ❌             |
| pico          | pico                                | ❌             |
| poke          | poke                                | ❌             |
| ps            | PlayStation                         | ✅             |
| ps2           | PlayStation 2                       | ✅             |
| psp           | PlayStation Portable                | ✅             |
| scummvm       | scummvm                             | ❌             |
| segacd        | Sega CD                             | ✅             |
| segasgone     | segasgone                           | ❌             |
| sgb           | sgb                                 | ❌             |
| sgfx          | sgfx                                | ❌             |
| snes          | Super Nintendo Entertainment System | ✅             |
| supervision   | supervision                         | ❌             |
| switch        | Nintendo Switch                     | ✅             |

## ⛏ Troubleshoot

* After the first installation, sometimes the RomM container can have problems connecting with the database. Restarting the RomM container may solve the problem.

## 🧾 References

* Complete [changelog](https://github.com/zurdi15/romm/blob/master/CHANGELOG.md)
