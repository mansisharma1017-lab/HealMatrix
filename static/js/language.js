function setLanguage(lang) {
  localStorage.setItem("lang", lang);
  applyLanguage();
}

function applyLanguage() {
  const lang = localStorage.getItem("lang") || "en";

  const sel = document.getElementById("langSelect");
  if (sel) sel.value = lang;

  const dict = {
    en: {
      home: "Home",
      login: "Login",
      register: "Register",
      logout: "Logout",
      download: "Download Report",
      history: "History",
      selectSymptoms: "Select Symptoms",
      predict: "Predict Disease",
    },
    hi: {
      home: "होम",
      login: "लॉगिन",
      register: "रजिस्टर",
      logout: "लॉगआउट",
      download: "रिपोर्ट डाउनलोड करें",
      history: "इतिहास",
      selectSymptoms: "लक्षण चुनें",
      predict: "बीमारी का अनुमान लगाएं",
    }
  };

  document.querySelectorAll("[data-key]").forEach(el => {
    const key = el.getAttribute("data-key");
    if (dict[lang][key]) {
      el.innerText = dict[lang][key];
    }
  });
}

window.addEventListener("load", applyLanguage);
