# NixieBot
Twitter Bot that drives smartsocket based alphanumeric neon tube display, hosted on Raspberry Pi.
Dependencies: Twython for Twitter comms, GrafixMagick for the gif making, Picamera and GPIO libraries.

Initial upload ... it's a bit nasty with far too many global vars etc, it just grew that way, refactor is on the cards :)

Should you wish to make your own you will need to:
Assemble hardware (Brace yourself for the price of B7971 tubes and mind you don't kill yourself or anyone else with the high voltage!) Or rewrite tweetOutWord to make the gif in another fashion (rendering perhaps)

Unless you want your bot getting traffic from this one you should change all references to "#Nixiebotshowme" in the code to another suitable hashtag of your choice.
Maybe change the greetings and scolds in makeStatusText to change the personality a bit too.
Command reference is at http://nixiebot.tumblr.com/ref

Nixiebotreader.py is a severely cut down version for collecting tweets and stashing them for later display while work is being done on the hardware, this might be a good starting point for those who want to do without all the hardware.

The user font file (ufont.txt) is an export from a character set drawn using this online character designer http://b7971.lucsmall.com/
be sure to select the "reverse order" button at the top of the page for smartsocket compatability.

