CS 334 Project 1 - Simple Client
Rofael Aleezada, Sam Lazrak, Jimmy Ward

Approach:
    The program starts with sending the "HELLO" message. The code then loops while receiving "STATUS" messages,
computing and replying with solutions. The loop continues until a message that doesn't contain "STATUS" is received.
If the message contains "BYE", the flag is extracted and printed, then the server disconnects and the program ends.

    Any code that could throw an exception (string parsing, opening and closing sockets, reading replies, etc.)
is handled with an exception that prints an appropriate error message.

Testing:
    Several cases were tested when this program was developed, including:
        * Passing correct parameters (./client -p 3001 odin.cs.uab.edu rofael)
        * Attempting to use an incorrect amount of parameters (./client odin)
        * Attempting to use strange/invalid BlazerIDs (./client -p 3001 odin.cs.uab.edu 00000yeahh)
        * Attempting to use SSL (./ client -s odin.cs.uab.edu rofael)
    Among other tests


Difficulties:
    The program was relatively straightforward to write, due to both the simplicity of the program, and Python's
lightweight sockets API that obfuscates a lot of the work needed in languages like C. While Python made SSL
as simple as a single line Ideally, we would have been able to test SSL connectivity to confirm it worked.
