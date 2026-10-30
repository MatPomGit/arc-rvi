# Słownik terminologiczny ARC-RVI

Terminologia do stosowania w polskojęzycznych opisach badań robotycznych.
Szczegóły metodologiczne i definicje operacyjne określa zawsze
[właściwy protokół](../experiments/README.md) oraz
[dokument odtwarzalności](reproducibility.md).

| Termin polski | Termin angielski | Znaczenie w projekcie |
| --- | --- | --- |
| Inspekcja wizualna | Visual inspection | Rejestrowanie i ocena dokumentacji obrazowej obiektu |
| Planowanie punktów widzenia | Viewpoint planning | Dobór pozycji kamery według jawnego kryterium jakości lub pokrycia |
| Pokrycie powierzchni | Surface coverage | Udział zadanej powierzchni z zaakceptowaną obserwacją, z ustalonym mianownikiem |
| Fikstura testowa | Test fixture | Syntetyczne, kontrolowane wejście służące sprawdzeniu zachowania kodu |
| Symulacja | Simulation | Eksperyment na zadeklarowanym modelu, nie wynik fizyczny |
| Walidacja fizyczna | Physical validation | Ocena na rzeczywistym systemie z referencyjnymi pomiarami i zgodą |
| Odtwarzalność | Reproducibility | Możliwość regeneracji wyniku z określonych danych, wersji i procedur |
| Powtarzalność | Repeatability | Zgodność ponawianych pomiarów w zdefiniowanych warunkach |
| Ograniczenie bezpieczeństwa | Safety constraint | Warunek, którego brak powoduje odrzucenie albo blokadę decyzji |
| Prawda referencyjna ewaluatora | Evaluator-only ground truth | Informacja do oceny wyniku, niedostępna metodzie planowania |
| Przerwanie bezpieczeństwa | Safety abort | Zakończenie próby z przyczyny zagrożenia, zachowywane w ewidencji |
| Rozłączność grup | Group-disjoint split | Podział danych rozdzielający obiekty, sesje lub rodziny scen |
| Estymand | Estimand | Formalnie określona wielkość będąca celem wnioskowania |
| Bramkowanie niepewności | Fail-closed gating | Brak wiarygodnego dowodu nie daje automatycznego przyzwolenia |

W tekstach angielskich zachowuj zwyczajową terminologię dziedziny.
Nie utożsamiaj powtarzalności z odtwarzalnością ani sukcesu testów
syntetycznych z potwierdzeniem empirycznym.
