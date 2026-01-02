Chrome Session Launcher - Project Overview

This is a desktop productivity application built with Python and PyQt6 that helps you organize and launch Chrome browser sessions with predefined sets of tabs.

What It Does
The app acts as a context switcher for web browsing - instead of manually opening multiple tabs every time you switch between different activities (work, entertainment, research), you can launch entire sets of tabs with one click.

Core Features
Session Management: Create, edit, and delete browsing sessions
Multi-Tab Launching: Open multiple URLs at once
YouTube Channel Switching: Special automation to switch YouTube accounts/channels
Custom Icons: Assign emojis to sessions for visual organization
Chrome Profile Support: Use specific Chrome profiles for different contexts

Technical Stack
Python 3 with PyQt6 (GUI framework)
Selenium WebDriver (browser automation)
JSON (configuration storage)
Windows batch file launcher

Key Files
src/context_launcher.py - Main application (461 lines)
src/config.json - Persistent session storage
launch.bat - Windows launcher script
old_code/ - Legacy PyQt5 version
Architecture

5 Main Classes:
ChromeLauncher - Selenium-based browser automation
LaunchWorker - Async thread for non-blocking launches
SessionDialog - Create/edit sessions
SettingsDialog - Configure Chrome/ChromeDriver paths
MainWindow - Main UI orchestration
The app follows an MVC-like pattern with clean separation between UI, business logic, and data storage. What would you like to work on? Some potential areas:
Adding new features
Improving existing functionality
Bug fixes
Code refactoring
Cross-platform support

CHAT:
Ok. I want to expand the scope of this project. Not only a chrome launcher, I want to use this to launch a "work session" of a certain type; so it could be a chrome window with certain tabs opened (thing that it already does), a vscode project in a certain folder, I dont have other idea in mind rn but it could be expanded more. 
It must serve to "manage" a litl bit my adhd/executive disfunction, place in a central place all the workflows and stuff i use more. 
Also for example i could remove some icons of software from my windows/macos toolbar, and put it into a section of this "launcher", to keep everything more clean
Currently i use both windows and macos, so possibly this should be multiplatform
It should be possible to "save" a certain workflow/software to open/state/etc in the program itself, from the gui, without reprogramming it. I'm thinking about saving "states" in a certain folder in json format; each json file for each session/scope (one for chrome sessions, one for programs to open i dunno etc)

Right now this is the interface:

Make a very detailed plan, in /context/plan.md that will allow us to develop this software, and expaind its current state. We can start from scratch if u want, taking only inspiration from original project, so we can create a better src folder structure, a better class organization, etc. It must be a very professional project

