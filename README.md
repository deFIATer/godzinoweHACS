# TGE ENEA - Integracja Home Assistant

Integracja Home Assistant dla danych o cenach energii TGE/ENEA z taryfy dynamicznej RDN.

## 🚀 Instalacja

### Przez HACS (Zalecane)

1. Otwórz HACS w Home Assistant
2. Przejdź do "Integrations"
3. Kliknij "Explore & Download Repositories"
4. Wyszukaj "TGE ENEA"
5. Zainstaluj integrację
6. Zrestartuj Home Assistant
7. Dodaj integrację przez Configuration > Integrations

### Ręczna instalacja

1. Skopiuj folder `custom_components/tge_enea` do katalogu `custom_components/` w Home Assistant
2. Zrestartuj Home Assistant
3. Dodaj integrację przez Configuration > Integrations

## ⚙️ Konfiguracja

Po dodaniu integracji będziesz mógł skonfigurować:
- **API URL**: Adres API (domyślnie: https://godzinowe.pl/api)

Integracja automatycznie pobiera dane co 5 minut dla aktualnej ceny i co godzinę dla całego dnia.

## 📊 Sensory

### Główne sensory:
- `sensor.tge_enea_aktualna_cena_enea` - Aktualna cena ENEA (zł/kWh)
- `sensor.tge_enea_klasyfikacja_ceny` - Klasyfikacja ceny (TANIUTKO/NISKA/ŚREDNIA/WYSOKA)
- `sensor.tge_enea_cena_tge` - Cena TGE (zł/kWh)
- `sensor.tge_enea_liczba_tanich_godzin` - Ile jest tanich godzin dziś
- `sensor.tge_enea_liczba_drogich_godzin` - Ile jest drogich godzin dziś

### Sensory binarne:
- `binary_sensor.tge_enea_energia_tania` - Czy energia jest teraz tania
- `binary_sensor.tge_enea_energia_droga` - Czy energia jest teraz droga

## 🛠️ Usługi (Services)

### `tge_enea.update_prices`
Ręczne odświeżenie danych o cenach.

### `tge_enea.get_cheap_hours`
Znajdź tanie godziny dla planowania.

**Parametry:**
- `hours_needed` (opcjonalny): Ile godzin taniego prądu potrzebujesz (domyślnie: 1)
- `date` (opcjonalny): Dla jakiego dnia (domyślnie: dziś)

**Przykład:**
```yaml
service: tge_enea.get_cheap_hours
data:
  hours_needed: 3
  date: "2025-09-30"
```

## 🏠 Przykłady automatyzacji

### Powiadomienie o taniej energii
```yaml
automation:
  - alias: "Powiadomienie - Energia tania"
    trigger:
      - platform: state
        entity_id: binary_sensor.tge_enea_energia_tania
        to: 'on'
    action:
      - service: notify.mobile_app_twoj_telefon
        data:
          title: "💡 Energia jest tania!"
          message: "Aktualna cena: {{ states('sensor.tge_enea_aktualna_cena_enea') }} zł/kWh"
```

### Włączanie bojlera gdy energia tania
```yaml
automation:
  - alias: "Bojler - włącz gdy tania energia"
    trigger:
      - platform: state
        entity_id: binary_sensor.tge_enea_energia_tania
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

Integracja automatycznie klasyfikuje ceny na podstawie dziennego rozkładu:

- **TANIUTKO**: Poniżej 0.2 zł/kWh (bardzo rzadkie)
- **NISKA**: 33% najtańszych cen w danym dniu
- **ŚREDNIA**: Środkowe 33% cen
- **WYSOKA**: 33% najdroższych cen w danym dniu

## 🔧 Wzór obliczania ceny ENEA

Integracja używa oficjalnego wzoru ENEA:
```
Cena brutto = (Cena TGE + Akcyza + Składnik B) × VAT
```
Gdzie:
- Akcyza = 0.005 zł/kWh
- Składnik B = 0.087 zł/kWh (według cennika ENEA)
- VAT = 23%

## 🐛 Zgłaszanie problemów

Problemy i sugestie można zgłaszać na [GitHub Issues](https://github.com/twoj_nick/tge-enea-hacs/issues).

## 📄 Licencja

MIT License