# Reprodukowalność i klasy dowodów: ARC-RVI

## Kontrakt przed badaniem

Należy określić hipotezę, protokół, prawa do danych, mierzalne punkty końcowe, kontrolę jakości, rozłączne zbiory danych oraz kryteria przerwania przed rozpoczęciem badania. Obecne testy inspekcji wizualnej są wykonywane offline. Adapter fizycznego robota nie jest aktywny. Wyniki symulacji nie stanowią dowodu bezpieczeństwa fizycznego ani potwierdzenia hipotezy.

## Dokumentowanie i kontrola

Dokumentacja badania powinna zawierać rewizję źródeł, wersje zależności, konfigurację sprzętu, pochodzenie i licencję danych, sumy kontrolne artefaktów, ziarna generatorów losowych, liczbę prób, metodę analizy, wyniki negatywne oraz ograniczenia. Należy weryfikować cytowania i DOI oraz przestrzegać zasad ochrony danych.

Rozróżnia się dowody koncepcyjne, syntetyczne, symulacyjne i empiryczne. Test jednostkowy nie stanowi dowodu skuteczności metody.

## Archiwizacja materiałów badawczych

Skrypty, raporty, wykresy, tabele i wyniki analiz dopuszczone do udostępnienia należy archiwizować wraz z metadanymi pochodzenia i sumami SHA-256. Dane zastrzeżone i duże zbiory wymagają odpowiedniego trwałego magazynu. Szczegóły określa [kontrakt reprodukowalności](../reproducibility.md#research-artifact-retention).

## Przed włączeniem wyniku do artykułu

Należy ocenić niezależność prób, ryzyko przecieku danych, niepewność, założenia wnioskowania, interpretację wyników i zgodność z protokołem. Raport powinien ujawniać braki danych, wyniki negatywne oraz brak walidacji, jeżeli dotyczy. Twierdzenia naukowe muszą odpowiadać klasie i zakresowi dostępnych dowodów.
