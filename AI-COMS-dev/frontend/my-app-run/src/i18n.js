import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import HttpBackend from 'i18next-http-backend';

i18n
  .use(HttpBackend) // load translations using http (default public folder)
  .use(initReactI18next)
  .init({
    lng: 'en', // default language
    fallbackLng: 'en',
    debug: true,

    interpolation: {
      escapeValue: false, // react already safes from xss
    },

    backend: {
      loadPath: '/locales/{{lng}}/translation.json',
    },    
  });

export default i18n;
