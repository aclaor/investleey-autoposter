Run python discord_poster.py
Traceback (most recent call last):
  File "/home/runner/work/investleey-autoposter/investleey-autoposter/discord_poster.py", line 179, in <module>
    main()
  File "/home/runner/work/investleey-autoposter/investleey-autoposter/discord_poster.py", line 160, in main
    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
                            ^^^^^^^^^
NameError: name 'WATCHLIST' is not defined
Error: Process completed with exit code 1.
