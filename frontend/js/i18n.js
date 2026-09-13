/**
 * RainSense Farmer - Multilingual Dictionary & Localization Engine
 * Supports: English (en), Telugu (te), Hindi (hi)
 */

const TRANSLATIONS = {
  en: {
    app_title: "RainSense Farmer",
    tagline: "Know Where It Rains. Know Your Soil. Make Better Farming Decisions.",
    nav_dashboard: "Dashboard",
    nav_map: "Rain Map",
    nav_locations: "My Locations",
    nav_history: "Rain History",
    nav_soil: "Soil Moisture",
    nav_insights: "AI Insights",
    nav_about: "About & Data Sources",
    demo_mode: "Demo Mode",
    greeting: "Good Day, Farmer 👋",
    greeting_sub: "Here is your live rain situation and soil intelligence.",
    hero_headline: "Know where the rain is.",
    hero_subheading: "Monitor rainfall, nearby rain activity, and soil moisture for your farming locations.",
    search_placeholder: "Search village, town, district in India...",
    btn_use_map: "Use Map",
    btn_my_locations: "My Locations",
    btn_try_demo: "Try Demo: Guntur Farm",
    badge_live: "LIVE / OBSERVED",
    badge_forecast: "FORECAST",
    badge_ai: "AI PREDICTION",
    badge_demo: "DEMO DATA",
    selected_farm: "Selected Location",
    monitoring_zone: "15 km Rain Monitoring Zone",
    status_no_rain: "No Rain",
    status_light_rain: "Light Rain",
    status_moderate_rain: "Moderate Rain",
    status_heavy_rain: "Heavy Rain",
    card_current_rain: "Current Rain Condition",
    card_nearby_rain: "15 km Rain Monitoring",
    card_soil_moisture: "Soil Moisture Intelligence",
    card_recent_rain: "Rainfall Received",
    card_ai_insight: "AI Farming Advisory",
    card_forecast: "Rainfall Forecast",
    nearest_rain: "Nearest Rain Activity",
    rain_coverage: "Rain Coverage (15 km Zone)",
    rain_movement: "Rain Movement Direction",
    surface_moisture: "Surface Soil Moisture",
    root_moisture: "Root Zone Soil Moisture",
    waterlogging_risk: "Waterlogging Risk",
    estimated_soil_label: "Estimated soil moisture (Hydrology model)",
    irrigation_advice: "Irrigation Advice",
    spraying_advice: "Spraying & Chemical Advice",
    field_work_advice: "Field Work Operations",
    btn_save_location: "Save This Location",
    btn_compare: "Compare Locations",
    locations_saved_counter: "locations saved",
    locations_max_alert: "You can save up to 5 farming locations.",
    rain_last_1h: "Last 1 Hour",
    rain_last_3h: "Last 3 Hours",
    rain_last_6h: "Last 6 Hours",
    rain_last_24h: "Last 24 Hours",
    rain_last_72h: "Last 72 Hours",
    chance_of_rain: "Chance of Rain",
    model_confidence: "Model Confidence",
    key_factors: "Key Weather Factors"
  },
  te: {
    app_title: "రెయిన్‌సెన్స్ ఫార్మర్",
    tagline: "వర్షం ఎక్కడ పడుతుందో తెలుసుకోండి. మీ నేల తేమను గ్రహించండి. మెరుగైన వ్యవసాయ నిర్ణయాలు తీసుకోండి.",
    nav_dashboard: "డ్యాష్‌బోర్డ్",
    nav_map: "వర్ష పటం",
    nav_locations: "నా పొలాలు",
    nav_history: "వర్ష చరిత్ర",
    nav_soil: "నేల తేమ",
    nav_insights: "AI సలహాలు",
    nav_about: "సమాచారం",
    demo_mode: "డెమో మోడ్",
    greeting: "నమస్కారం రైతు సోదరా 👋",
    greeting_sub: "మీ పొలం మరియు పరిసరాల వర్ష సమాచారం ఇక్కడ ఉంది.",
    hero_headline: "వర్షం ఎక్కడ పడుతుందో ఖచ్చితంగా తెలుసుకోండి.",
    hero_subheading: "మీ పొలం దగ్గర వర్షం, 15 కి.మీ పరిధిలోని వర్ష కదలికలు మరియు నేల తేమను గమనించండి.",
    search_placeholder: "గ్రామం, పట్టణం, లేదా జిల్లా పేరు వెతకండి...",
    btn_use_map: "పటంలో చూడండి",
    btn_my_locations: "నా పొలాలు",
    btn_try_demo: "డెమో: గుంటూరు పొలం",
    badge_live: "ప్రత్యక్ష పరిశీలన",
    badge_forecast: "వాతావరణ అంచనా",
    badge_ai: "AI విశ్లేషణ",
    badge_demo: "డెమో సమాచారం",
    selected_farm: "ఎంచుకున్న పొలం",
    monitoring_zone: "15 కి.మీ వర్ష పర్యవేక్షణ పరిధి",
    status_no_rain: "వర్షం లేదు",
    status_light_rain: "తేలికపాటి వర్షం",
    status_moderate_rain: "మోస్తరు వర్షం",
    status_heavy_rain: "భారీ వర్షం",
    card_current_rain: "ప్రస్తుత వర్ష పరిస్థితి",
    card_nearby_rain: "15 కి.మీ పరిధిలో వర్షం",
    card_soil_moisture: "నేల తేమ స్థాయి",
    card_recent_rain: "కురిసిన వర్షపాతం",
    card_ai_insight: "రైతుకు AI సలహాలు",
    card_forecast: "రాబోయే వర్ష సూచన",
    nearest_rain: "సమీపంలో కురుస్తున్న వర్షం",
    rain_coverage: "15 కి.మీ పరిధిలో వర్ష విస్తీర్ణం",
    rain_movement: "వర్ష మేఘాల దిశ",
    surface_moisture: "పై పొర నేల తేమ",
    root_moisture: "వేరు వ్యవస్థ నేల తేమ",
    waterlogging_risk: "నీరు నిలిచే ప్రమాదం",
    estimated_soil_label: "అంచనా వేసిన నేల తేమ (శాటిలైట్ మోడల్)",
    irrigation_advice: "నీటిపారుదల సలహా",
    spraying_advice: "మందుల పిచికారీ సలహా",
    field_work_advice: "పొలం పనులు",
    btn_save_location: "ఈ పొలాన్ని భద్రపరచండి",
    btn_compare: "పొలాల పోలిక",
    locations_saved_counter: "పొలాలు భద్రపరచబడ్డాయి",
    locations_max_alert: "మీరు గరిష్టంగా 5 పొలాలను మాత్రమే భద్రపరచగలరు.",
    rain_last_1h: "గడచిన 1 గంటలో",
    rain_last_3h: "గడచిన 3 గంటలలో",
    rain_last_6h: "గడచిన 6 గంటలలో",
    rain_last_24h: "గడచిన 24 గంటలలో",
    rain_last_72h: "గడచిన 72 గంటలలో",
    chance_of_rain: "వర్ష సూచన శాతం",
    model_confidence: "AI విశ్వసనీయత",
    key_factors: "ముఖ్య వాతావరణ అంశాలు"
  },
  hi: {
    app_title: "रेनसेन्स फार्मर",
    tagline: "जानिए बारिश कहाँ हो रही है। अपनी मिट्टी को समझें। बेहतर खेती के फैसले लें।",
    nav_dashboard: "डैशबोर्ड",
    nav_map: "वर्षा मानचित्र",
    nav_locations: "मेरे खेत",
    nav_history: "वर्षा इतिहास",
    nav_soil: "मिट्टी की नमी",
    nav_insights: "AI सलाह",
    nav_about: "डेटा स्रोत",
    demo_mode: "डेमो मोड",
    greeting: "नमस्ते किसान भाई 👋",
    greeting_sub: "यहाँ आपके खेत की लाइव वर्षा और मिट्टी की जानकारी है।",
    hero_headline: "जानिए बारिश कहाँ हो रही है।",
    hero_subheading: "अपने खेतों के आसपास बारिश, 15 किमी क्षेत्र की वर्षा और मिट्टी की नमी पर नज़र रखें।",
    search_placeholder: "गाँव, कस्बा या जिले का नाम खोजें...",
    btn_use_map: "नक्शे पर देखें",
    btn_my_locations: "मेरे खेत",
    btn_try_demo: "डेमो: गुंटूर खेत",
    badge_live: "लाइव अवलोकन",
    badge_forecast: "मौसम पूर्वानुमान",
    badge_ai: "AI भविष्यवाणी",
    badge_demo: "डेमो डेटा",
    selected_farm: "चुना हुआ खेत",
    monitoring_zone: "15 किमी वर्षा निगरानी क्षेत्र",
    status_no_rain: "बारिश नहीं",
    status_light_rain: "हल्की बारिश",
    status_moderate_rain: "मध्यम बारिश",
    status_heavy_rain: "तेज बारिश",
    card_current_rain: "वर्तमान बारिश की स्थिति",
    card_nearby_rain: "15 किमी दायरे में बारिश",
    card_soil_moisture: "मिट्टी की नमी",
    card_recent_rain: "हाल की बारिश",
    card_ai_insight: "AI कृषि सलाह",
    card_forecast: "बारिश का पूर्वानुमान",
    nearest_rain: "सबसे नज़दीक बारिश",
    rain_coverage: "15 किमी दायरे में वर्षा कवरेज",
    rain_movement: "बादलों की गति की दिशा",
    surface_moisture: "सतह की मिट्टी की नमी",
    root_moisture: "जड़ क्षेत्र की नमी",
    waterlogging_risk: "जलभराव का जोखिम",
    estimated_soil_label: "अनुमानित मिट्टी की नमी (उपग्रह मॉडल)",
    irrigation_advice: "सिंचाई सलाह",
    spraying_advice: "कीटनाशक छिड़काव सलाह",
    field_work_advice: "खेत के कार्य",
    btn_save_location: "यह खेत सहेजें",
    btn_compare: "खेतों की तुलना",
    locations_saved_counter: "खेत सहेजे गए",
    locations_max_alert: "आप अधिकतम 5 खेत ही सहेज सकते हैं।",
    rain_last_1h: "पिछले 1 घंटे में",
    rain_last_3h: "पिछले 3 घंटे में",
    rain_last_6h: "पिछले 6 घंटे में",
    rain_last_24h: "पिछले 24 घंटे में",
    rain_last_72h: "पिछले 72 घंटे में",
    chance_of_rain: "बारिश की संभावना",
    model_confidence: "AI विश्वसनीयता",
    key_factors: "मुख्य मौसमी कारक"
  }
};

class I18nManager {
  constructor() {
    this.currentLang = localStorage.getItem("rainsense_lang") || "en";
  }

  setLanguage(lang) {
    if (TRANSLATIONS[lang]) {
      this.currentLang = lang;
      localStorage.setItem("rainsense_lang", lang);
      this.applyTranslations();
    }
  }

  t(key) {
    const dict = TRANSLATIONS[this.currentLang] || TRANSLATIONS.en;
    return dict[key] || TRANSLATIONS.en[key] || key;
  }

  applyTranslations() {
    document.querySelectorAll("[data-i18n]").forEach(elem => {
      const key = elem.getAttribute("data-i18n");
      elem.textContent = this.t(key);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(elem => {
      const key = elem.getAttribute("data-i18n-placeholder");
      elem.placeholder = this.t(key);
    });
  }
}

window.i18n = new I18nManager();
