daedalus Indoor Positioning System

Das Programm hat folgende Abhängigkeiten:
python3-gi python3-gi-cairo python3-all python3-regex python3-serial python3-gobject

die multilat-library muss für die entspechende Plattform kompiliert werden. Das kann unter Linux mit diesen beiden Befehlen gemacht werden:
gcc -c -fPIC -O3 multilat.c
gcc -shared -o multilat.so multilat.
