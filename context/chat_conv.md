Part of chatgpt conversation:

I want to build a system that let me open automatically a certain browser session, with some tabs opened into it (i use chrome)
For ex, i click on a bat file or launch a command and it opens chrome with the following tabs opened into it: netflix, amazon prime video, mubi

Another bat file: it opens a window of youtube, and it switch to a specific yt channel that i have (I have multiple yt channels on my yt acount, each channel with its own playlists). For this i think i need a python script, in order to switch to a certain yt channel
You're basically designing a "context launcher" — a small automation system to open Chrome in a specific “mode” or “session” depending on your activity (e.g. Relaxation mode, Study mode, Music mode).

You could expand this into a small launcher system:
A Python GUI (Tkinter or PyQt) that shows buttons: “Relax”, “Study”, “Music”.
Each button triggers one of these .bat or Python scripts.
I would like to build a similar app described by this chatgpt conversation. I want to build the version with pyqt, obviously no more batch file, everything coded into the app

The app would let me to launch the various "sessions" (in terms of tab opened) in chrome; when sessions are yt sessions it would open the channel related to it (switching the yt channel; not opening it with a url, i want to SWITCH the channel, they are under the same email but different yt channels)
I dunno if i need to encode the various possible channels into a json file, things would be more customizable