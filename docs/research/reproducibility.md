# Reprodukowalność i klasy dowodów: arc-rvi

**Wersja:** 1.0.0 (2026-10-31). Uzupełnia [AGENTS.md](../../AGENTS.md), [cykl agenta](../development/agent-workflow.md) i istniejące protokoły. Nie ustanawia nowego rejestru.

## Kontrakt przed badaniem
ARC-RVI: obecnie dostępne są offline testy inspekcji wizualnej, a adapter robota fizycznego nie jest aktywny. Nie przedstawiaj jakości zdjęć syntetycznych, planowania widoków lub testów stabilności podpór jako fizycznej demonstracji bezpieczeństwa. Próba humanoida wymaga oddzielnej autoryzacji i zabezpieczeń.

Przed analizą odczytaj aktualny stan projektu, hipotezę, protokół, prawa do danych i istniejące źródła prawdy. Przygotuj z góry mierzalne wyniki, kontrolę jakości, rozdział danych treningowych, walidacyjnych i testowych oraz kryteria przerwania. Brak uprawnień, danych albo decyzji etycznej oznacz BLOCKED, nie wykonane badanie. Nie przekształcaj hipotez, prerejestracji DRAFT ani wyników symulacji w dowody empiryczne.

## Dokumentowanie i kontrola
Zapisz SHA źródeł, komendy, wersje zależności, sprzęt, dane, źródło i licencję, identyfikatory oraz hashe artefaktów, seeds, liczbę prób, metodę analizy, wyniki negatywne, odchylenia i ograniczenia. Przestrzegaj istniejącej polityki prywatności, retencji i repozytoryjnego rejestru dowodów. Nie dodawaj równoległego ledgeru, nie przesyłaj danych uczestników na GitHub. Cytowania i DOI weryfikuj w wiarygodnych źródłach.

Rozróżniaj: NOT_RUN, UNAVAILABLE, FAIL, PASS dla testów kodu; conceptual, synthetic, simulation, empirical dla dowodów; proposed, implemented, tested, merged, deployed dla cyklu życia. Testy jednostkowe nie dowodzą skuteczności metody. Merge i publikacja MkDocs nie dowodzą walidacji fizycznej ani zgody na zbieranie danych.

## Przed włączeniem wyniku do artykułu
Sprawdź niezależność prób, leakage, niepewność, podstawy wnioskowania, interpretację wyników i spójność z manuskryptem. Ujawnij brak walidacji, brak danych i wyniki ujemne. Przejrzyj aktualne GitHub Issues i reguły projektu. Każda zmiana przechodzi testy exact-SHA, właściwy review i osobne zatwierdzenie działań chronionych; komentarz tego samego konta nie zastępuje formalnego GitHub approval.
