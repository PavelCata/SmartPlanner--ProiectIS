SmartPlanner – Smart Task Planning System

Descriere generala

SmartPlanner este o aplicatie web care ii ajuta pe utilizatori sa isi organizeze activitatile zilnice mai usor si mai eficient. Aplicatia nu se limiteaza doar la salvarea taskurilor, ci incearca sa le organizeze automat, sa le analizeze si sa ofere sugestii si notificari utile, astfel incat utilizatorul sa nu uite lucruri importante.

Functionalitati principale

Aplicatia are patru functionalitati de baza. Prima este organizarea inteligenta a taskurilor, unde utilizatorii pot crea activitati cu intervale orare si nivel de importanta, iar sistemul muta automat taskurile in caz de conflicte. A doua este partea de statistici, care arata ce tipuri de taskuri sunt realizate cel mai des si cum este folosit timpul. A treia este modulul colaborativ, prin care utilizatorii pot avea prieteni si pot lucra impreuna la taskuri. A patra functionalitate este sistemul de notificari, care informeaza utilizatorii despre evenimente importante si trimite alerte atunci cand sunt detectate situatii relevante.

Autentificare si administrare

Utilizatorii se pot inregistra si autentifica in aplicatie, iar parolele sunt stocate in siguranta. Exista roluri diferite, cum ar fi user si admin. Administratorii pot gestiona conturile si pot restrictiona accesul atunci cand este necesar.

Tehnologii

SmartPlanner este realizat in Python folosind Flask. Baza de date este MySQL, iar comunicarea cu aceasta se face prin SQLAlchemy. Interfata grafica este construita cu HTML, CSS si Jinja2, iar aplicatia foloseste arhitectura MVC.

Design Patterns

In aplicatie sunt folosite mai multe design patterns: Proxy pentru controlul accesului, Singleton pentru configurare si baza de date, Observer pentru sistemul de notificari si Builder pentru crearea flexibila a taskurilor.

Rulare

Aplicatia poate fi pornita local cu comanda python main.py, iar dupa pornire este accesibila la adresa http://127.0.0.1:5000
.

Echipa

Proiectul a fost realizat de Denis, Gunter, Andreea si Catalin.
