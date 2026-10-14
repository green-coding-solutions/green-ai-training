## Explaination

This file is an ouput of an LLM query but also serves as basis for a new LLM query.

Use it as prompt template. Fill in your benchmarks into `FILL_IN_YOUR_PATHS_TO_THE_BENCHMARKS`

## Prompt Template

Please create SQL insert statements for the benchmarks: {FILL_IN_YOUR_PATHS_TO_THE_BENCHMARKS}

To do so read the file `software_tasks_insert.example.sql` and ignore any comments in it starting with the
standard SQL comment syntax `--`

Then create a new file called `software_tasks_insert.sql` with the new benchmarks as specified by the user above.

## Categories

The categories possible are the following:

ID   NAME
---------
2    Linux
6    GUI Applications
3    Windows
4    Websites
1    macOS
7    AI
12    Code Editors
5    Command Line Programs
8    AI Inference
9    AI Training
10    Compression Tools
11    Network Client
13    Office Solutions
14    Database
15    SQL-Database
16    No-SQL Database
17    Web CMS
18    Python based
19    PHP based
20    Library
22    Virtualization/Containerization
24    Key Value Stores
25    Pdf Viewers
32    Website User Journey
33    Micro-benchmarks
34    Image Processing
35    Browser Rendering
36    Video Players
37    Terminal Emulators
38    Email Clients
39    Chat Clients
40    Word Processors
41    Spreadsheets

## Softwares

This is the amount of softwares already in the DB. Please try to create software_tasks below already
existing software if you think this is a match.

Otherwise create new softwares in the softwares table as shown in the example `software_tasks_insert.example.sql`

Name    category_ids
-------------------
emacs    {12,5,2}
nano    {12,5,2}
vim    {12,5,2}
QEMU    {1,2,22}
Docker    {1,2,22}
Oracle DB    {2,14,15}
CockroachDB    {2,14,15}
Nextcloud    {1,2,6,13}
wget    {1,2,5,20,11}
Python    {2,18,33}
python-requests    {1,2,3,5,20,11}
LZIP    {1,2,5,10}
ZStd    {1,2,5,10}
bzip2    {1,2,5,10}
MariaDB    {2,14,15}
Wordpress    {2,17,19}
Wagtail    {2,17,18}
MySQL    {2,14,15}
Django    {2,17,18}
curl    {1,2,3,5,20,11}
PostgreSQL    {2,14,15,33}
gzip    {1,2,5,10}
XZ    {1,2,5,10}
Cloud Hypervisor    {1,2,22}
babi    {12,5,2}
brotli    {1,2,5,10}
lz4    {1,2,5,10}
p7zip    {1,2,5,10}
Redis    {2,14,24}
DB2    {2,14,15}
MsSQL    {2,14,15}
DragonflyDB    {2,14,24}
Memcached    {2,14,24}
KeyDB    {2,14,24}
Valkey    {2,14,24}
Evince    {25,2,6}
atril    {25,2,6}
Firefox    {25,2,6}
xpdf    {25,2,6}
qpdfview    {25,2,6}
okular    {25,2,6}
Bash Quoting Pattern Matching    {2,5,33}
Browser Animation Rendering Cost (CSS vs JS)    {2,35,33}
Image Format Encoding Cost    {2,5,34,33}
Image Format Rendering Cost (Headful Browser)    {2,34,35,33}
AbiWord    {2,6,13,40}
Alacritty    {2,6,37}
Android Studio    {2,6,12}
Apache OpenOffice Calc    {2,6,13,41}
Apache OpenOffice Writer    {2,6,13,40}
Betterbird    {2,6,11,38}
BlueMail    {2,6,11,38}
Calligra Words    {2,6,13,40}
Claws Mail    {2,6,11,38}
Collabora Office    {2,6,13,40}
Eclipse IDE    {2,6,12}
Element Desktop    {2,6,11,39}
FluffyChat    {2,6,11,39}
Fractal    {2,6,11,39}
GNOME Evolution    {2,6,11,38}
GNOME Terminal    {2,6,37}
Gnumeric    {2,6,13,41}
IntelliJ IDEA    {2,6,12}
JupyterLab    {2,6,12,18}
kitty    {2,6,37}
KMail    {2,6,11,38}
Konsole    {2,6,37}
LibreOffice Calc    {2,6,13,41}
LibreOffice Writer    {2,6,13,40}
Mailspring    {2,6,11,38}
mlterm    {2,6,37}
Mozilla Thunderbird    {2,6,11,38}
mpv    {2,6,36}
Neovim    {2,5,12}
nheko    {2,6,11,39}
Parole    {2,6,36}
pterm    {2,6,37}
PyCharm    {2,6,12}
rxvt-unicode    {2,6,37}
SchildiChat    {2,6,11,39}
SMPlayer    {2,6,36}
SoftMaker FreeOffice TextMaker    {2,6,13,40}
st    {2,6,37}
Sublime Text    {2,6,12}
Totem    {2,6,36}
Visual Studio Code    {2,6,12}
VLC media player    {2,6,36}
xterm    {2,6,37}

## Software Tasks

For every benchmark specified by the user please create the appropriate software_tasks.

They should map to a software which you either choose from above or have created anew.

Typically every phase in a usage scenario benchmark maps to a software_task.
If it makes sense please also create for the whole usage scenario a run that uses the magic `[RUNTIME]` phase
and specifies the full workflow. However be aware that it does not always makes sense.

Example:
- In `usage_scenario-lazy.yml` it does not make sense to create an entry for the `[RUNTIME]` phase as the steps
measure polar opposite behaviour and it makes no sense to see the aggregate values
- But in `usage_scenario-double-quotes.yml` using the `[RUNTIME]` phase is very helpful as all steps measure
incrementing load and it is interesting to also the the totals over all load steps.

If you create a `[RUNTIME]` phase give it a descriptive name what the sum of all the sub-phases means
Also: If a usage_scenario only has one non-hidden flow step in total then please never use the `[RUNTIME]` phase but only
use the single non hidden phase and its name.





## Remarks

- Phase names are stored without the numeric prefix (see `software_tasks_insert.example.sql`: `regexp_replace(p.phase, '^[0-9]+_', '')`)
- Hidden flows (e.g. "Close", "Report filesystem size") should never be in the insert statement

