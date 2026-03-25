### Hold button issues

(CC_RVGAI) C:\Users\Admin\anaconda3\envs\CC_Emu>python chat_with_emulator.py
🎮 Enhanced SNES Emulator AI Chat
==================================================
Features:
✅ Fixed hold button functionality with proper duration support
✅ Multi-command sequences: 'go up for 3 seconds then go left'
✅ Auto port detection and better error handling
✅ Launch, connect, and intro skip automation

Checking for Flask server...
✅ Found Flask server on port 5000
Type 'quit' to exit

You: hold up for 10 seconds
🤖 AI: 🔧 Executing: hold_button({'button_name': 'Up', 'duration': 10})
I'm sorry, but there seems to be an error in executing your command. Let's give it another try. I'll hold the "Up" button for 10 seconds.

You: try again. Can yo ushow me the error?
🤖 AI: 🔧 Executing: hold_button({'button_name': 'Up', 'duration': 10})
I'm afraid we've encountered the same error again. The error message is: "Expecting value: line 1 column 1 (char 0)". This typically means there's a problem with the JSON response from the emulator. It might be a transient issue or something more serious. I would recommend restarting the emulator or checking its connectivity.

You: press x
🤖 AI: 🔧 Executing: press_button({'button_name': 'X'})
The "X" button has been pressed successfully. Let me know if you need any other actions to be performed in the game.