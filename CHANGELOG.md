# Changelog

Wszystkie istotne zmiany w tym projekcie będą dokumentowane w tym pliku.

## [1.0.0] - 2025-09-29

### Dodano
- Pierwsza wersja integracji TGE ENEA dla Home Assistant
- Sensory dla aktualnej ceny ENEA i klasyfikacji
- Binary sensory dla taniej/drogiej energii  
- Usługi do odświeżania danych i znajdowania tanich godzin
- Konfiguracja przez GUI (Config Flow)
- Automatyczna klasyfikacja cen na podstawie przedziałów dziennych
- Wsparcie dla wzoru cenowego ENEA z oficjalnymi składnikami
- Dokumentacja po polsku

### Funkcje
- Pobieranie danych z API co 5 minut (aktualna cena) i co godzinę (dane całego dnia)
- Klasyfikacja: TANIUTKO/NISKA/ŚREDNIA/WYSOKA
- Attributes z dodatkowymi informacjami (przedział godzinowy, wolumen, progi)
- Obsługa błędów i retry logic
- Walidacja API podczas konfiguracji