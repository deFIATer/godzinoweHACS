# godzinowe.pl - Integracja Home Assistant

Integracja Home Assistant dla godzinowych cen energii z API godzinowe.pl.

API zwraca czyste ceny rynkowe TGE w `zł/kWh`. Integracja potrafi dodatkowo doliczyć Twoje własne składniki: VAT/mnożnik ceny rynkowej, dystrybucję G11/G12/G12w/G13 oraz stałą dopłatę `zł/kWh` na opłaty jakościowe, OZE, kogeneracyjne, marżę sprzedawcy itp.

## 🚀 Instalacja

### Przez HACS (Zalecane)

1. Otwórz HACS w Home Assistant
2. Przejdź do "Integrations"
3. Kliknij "Explore & Download Repositories"
4. Wyszukaj "godzinowe.pl"
5. Zainstaluj integrację
6. Zrestartuj Home Assistant
7. Dodaj integrację przez Configuration > Integrations

### Ręczna instalacja

1. Skopiuj folder `custom_components/godzinowe_pl` do katalogu `custom_components/` w Home Assistant
2. Zrestartuj Home Assistant
3. Dodaj integrację przez Configuration > Integrations

## ⚙️ Konfiguracja

Po dodaniu integracji będziesz mógł skonfigurować:
- **API URL**: Adres API (domyślnie: `https://godzinowe.pl/api.php`)

W opcjach integracji ustawisz:
- **Typ taryfy**: `g11`, `g12`, `g12w` albo `g13`
- **Mnożnik ceny rynkowej**: domyślnie `1.23`, czyli cena rynkowa z VAT
- **Stała dopłata**: jedna wartość `zł/kWh` na dodatkowe składniki
- **Stawki dystrybucji**: osobno dla G11, dzień/noc dla G12/G12w oraz szczyt przedpołudniowy, szczyt popołudniowy i pozaszczyt dla G13
- **Okna godzinowe G12/G12w**: godziny początku i końca strefy dziennej oraz nocnej

Integracja automatycznie pobiera aktualną godzinę, cały dzień dzisiejszy i dane na jutro. Jeśli API jeszcze nie ma danych na jutro, sensor jutra ma stan `unavailable`, a w atrybucie `message` pojawia się informacja z API.

## 📊 Sensory

### Główne sensory:
- `sensor.aktualna_cena_rynkowa` - Aktualna czysta cena rynkowa z API (zł/kWh)
- `sensor.aktualna_cena_z_taryfa` - Aktualna cena po doliczeniu Twoich opcji taryfowych (zł/kWh)
- `sensor.klasyfikacja_ceny` - Klasyfikacja ceny (UJEMNA/ZERO/BARDZO NISKA/NISKA/ŚREDNIA/WYSOKA/BARDZO WYSOKA/EKSTREMALNA)
- `sensor.cena_tge` - Cena TGE (zł/kWh)
- `sensor.liczba_tanich_godzin_dzis` - Ile jest tanich godzin dziś
- `sensor.liczba_drogich_godzin_dzis` - Ile jest drogich godzin dziś
- `sensor.liczba_tanich_godzin_jutro` - Ile jest tanich godzin jutro
- `sensor.liczba_drogich_godzin_jutro` - Ile jest drogich godzin jutro
- `sensor.plan_cen_dzis` - Pełny plan godzinowy dla dziś w atrybucie `records`
- `sensor.plan_cen_jutro` - Pełny plan godzinowy dla jutra w atrybucie `records`

Sensory planu dnia mają przydatne atrybuty:
- `records` - wszystkie godziny z `price_per_kwh`, `classification`, `market_price_gross`, `tariff_rate`, `total_price`
- `cheap_hours` i `expensive_hours` - lista tanich i drogich godzin
- `cheapest_hours` i `most_expensive_hours` - najtańsze i najdroższe godziny po doliczeniu taryfy
- `statistics` - statystyki ceny rynkowej
- `total_price_statistics` - statystyki ceny po doliczeniu taryfy
- `completeness` - kompletność danych z API

### Sensory binarne:
- `binary_sensor.energia_tania` - Czy energia jest teraz tania
- `binary_sensor.energia_droga` - Czy energia jest teraz droga

## 🛠️ Usługi (Services)

### `godzinowe_pl.update_prices`
Ręczne odświeżenie danych o cenach.

### `godzinowe_pl.get_cheap_hours`
Znajdź tanie godziny dla planowania.

**Parametry:**
- `hours_needed` (opcjonalny): Ile godzin taniego prądu potrzebujesz (domyślnie: 1)
- `date` (opcjonalny): Dla jakiego dnia (domyślnie: dziś)

**Przykład:**
```yaml
service: godzinowe_pl.get_cheap_hours
data:
  hours_needed: 3
  date: "2025-09-30"
```

## 📊 Przykłady dashboardów

Gotowe przykłady Lovelace YAML znajdują się w katalogu [`examples`](examples/).

- [`examples/energy_prices_view.yaml`](examples/energy_prices_view.yaml) - pojedynczy widok do wklejenia w edytorze YAML widoku.
- [`examples/energy_prices_wide_view.yaml`](examples/energy_prices_wide_view.yaml) - szeroki widok `panel: true` z wykresem 48h.
- [`examples/energy_prices_today_view.yaml`](examples/energy_prices_today_view.yaml) - szeroki widok tylko dla dzisiejszych cen.
- [`examples/energy_prices_tomorrow_view.yaml`](examples/energy_prices_tomorrow_view.yaml) - szeroki widok tylko dla jutrzejszych cen.
- [`examples/energy_prices_dashboard.yaml`](examples/energy_prices_dashboard.yaml) - pełna konfiguracja dashboardu do wklejenia w surowej konfiguracji dashboardu.

Do wykresów godzinowych wymagany jest `apexcharts-card`, który można zainstalować przez HACS jako kartę frontendową. Zwykła karta historii Home Assistant pokazuje historię stanów encji, ale nie narysuje pełnego planu dnia z atrybutu `records`.

Jeśli edytujesz konkretny widok w Home Assistant, użyj pliku `energy_prices_view.yaml`. Jeśli wklejasz konfigurację całego dashboardu przez Raw configuration editor, użyj `energy_prices_dashboard.yaml`.

Pole `path` jest adresem URL widoku i musi być unikalne w ramach dashboardu. Jeśli Home Assistant pokazuje błąd, że widok z tym samym adresem URL już istnieje, zmień np. `path: ceny-energii` na inną wartość albo usuń/zmień stary widok z takim samym adresem.

## 🏠 Przykłady automatyzacji

### Powiadomienie o taniej energii
```yaml
automation:
  - alias: "Powiadomienie - Energia tania"
    trigger:
      - platform: state
        entity_id: binary_sensor.energia_tania
        to: 'on'
    action:
      - service: notify.mobile_app_twoj_telefon
        data:
          title: "💡 Energia jest tania!"
          message: "Aktualna cena z taryfą: {{ states('sensor.aktualna_cena_z_taryfa') }} zł/kWh"
```

### Włączanie bojlera gdy energia tania
```yaml
automation:
  - alias: "Bojler - włącz gdy tania energia"
    trigger:
      - platform: state
        entity_id: binary_sensor.energia_tania
        to: 'on'
    condition:
      - condition: time
        after: "22:00:00"
        before: "06:00:00"
    action:
      - service: switch.turn_on
        entity_id: switch.bojler
```

## 📈 Klasyfikacja cen

Integracja automatycznie klasyfikuje ceny na podstawie stałych progów `zł/kWh`:

- **UJEMNA**: poniżej 0 zł/kWh
- **ZERO**: 0 zł/kWh lub po zaokrągleniu do 2 miejsc wychodzi 0.00
- **BARDZO NISKA**: od 0.01 do poniżej 0.15 zł/kWh
- **NISKA**: od 0.15 do poniżej 0.35 zł/kWh
- **ŚREDNIA**: od 0.35 do poniżej 0.55 zł/kWh
- **WYSOKA**: od 0.55 do poniżej 0.75 zł/kWh
- **BARDZO WYSOKA**: od 0.75 do poniżej 1.5 zł/kWh
- **EKSTREMALNA**: od 1.5 zł/kWh

### Wybór najtańszej godziny jutro
```yaml
template:
  - sensor:
      - name: "Najtańsza godzina jutro"
        state: >
          {% set h = state_attr('sensor.plan_cen_jutro', 'cheapest_hours') %}
          {{ h[0].hour if h else 'brak danych' }}
        attributes:
          total_price: >
            {% set h = state_attr('sensor.plan_cen_jutro', 'cheapest_hours') %}
            {{ h[0].total_price if h else none }}
```

## 🔧 Wzór obliczania ceny z taryfą

Integracja liczy:
```
Cena z taryfą = Cena rynkowa z API × mnożnik + stawka dystrybucji dla godziny + stała dopłata
```

Domyślnie mnożnik wynosi `1.23`, a stawki dystrybucji i stała dopłata wynoszą `0`, więc możesz wpisać dokładnie swoje składniki z faktury albo cennika operatora.

## 🐛 Zgłaszanie problemów

Problemy i sugestie można zgłaszać na GitHub Issues w repozytorium integracji.

## 📄 Licencja

MIT License
