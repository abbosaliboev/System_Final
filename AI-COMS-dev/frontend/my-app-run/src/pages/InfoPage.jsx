// File: InfoPage.jsx
import React, { useState } from "react";
import { useTranslation } from "react-i18next";

// Styles
import "../assets/components/_info.scss";

const InfoPage = () => {
  const { t } = useTranslation(); // Translation hook
  const [searchQuery, setSearchQuery] = useState("");

  // System general info object
  const systemInfo = {
    name: "Safety Monitoring System",
    version: "2.3.1",
    lastUpdated: "2025-05-20",
    description: t("system_description"),
    features: [
      t("feature_realtime"),
      t("feature_alerts"),
      t("feature_reports"),
      t("feature_heatmap"),
      t("feature_mobile"),
    ],
    stats: {
      totalUsers: 1250,
      activeIncidents: 45,
      resolvedIncidents: 320,
      uptime: "99.9%",
    },
  };

  // Contact information items
  const contactInfo = [
    { id: 1, type: t("email"), value: "support@safetysystem.com", icon: "bi bi-envelope-fill" },
    { id: 2, type: t("phone"), value: "070-555-1234", icon: "bi bi-telephone-fill" },
    { id: 3, type: t("address"), value: "123, Seoul, South Korea", icon: "bi bi-geo-alt-fill" },
  ];

  // Frequently Asked Questions
  const faqData = [
    { id: 1, question: t("faq_1_q"), answer: t("faq_1_a") },
    // You can add more FAQs here
  ];

  // Filtered FAQ list based on search input
  const filteredFaq = faqData.filter((item) =>
    item.question.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="info-page">
      
      {/* Header with title and search bar */}
      <div className="info-header">
        <h5 className="fw-bold">{t("system_info")}</h5>
        <input
          type="text"
          placeholder={t("search_faq")}
          className="form-control search-input"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* System Information Card */}
      <div className="card system-card">
        <div className="card-body">
          <h5 className="card-title">{systemInfo.name}</h5>
          <p className="text-muted">
            {t("version")}: {systemInfo.version} | {t("updated")}: {systemInfo.lastUpdated}
          </p>
          <p className="card-text">{systemInfo.description}</p>

          {/* Feature list */}
          <h6 className="fw-bold mt-3">{t("features")}</h6>
          <ul className="list-unstyled">
            {systemInfo.features.map((feature, index) => (
              <li key={index} className="mb-2">
                <i className="bi bi-check-circle-fill text-success me-2"></i>
                {feature}
              </li>
            ))}
          </ul>

          {/* System statistics */}
          <h6 className="fw-bold mt-3">{t("stats")}</h6>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">{t("total_users")}:</span>
              <span className="stat-value">{systemInfo.stats.totalUsers}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">{t("active_incidents")}:</span>
              <span className="stat-value">{systemInfo.stats.activeIncidents}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">{t("resolved_incidents")}:</span>
              <span className="stat-value">{systemInfo.stats.resolvedIncidents}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">{t("uptime")}:</span>
              <span className="stat-value">{systemInfo.stats.uptime}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Contact Card */}
      <div className="card contact-card">
        <div className="card-body">
          <h5 className="card-title">{t("contact_center")}</h5>
          <div className="contact-grid">
            {contactInfo.map((item) => (
              <div key={item.id} className="contact-item">
                <i className={`${item.icon} me-2`}></i>
                <span className="contact-type">{item.type}:</span>
                <span className="contact-value">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="faq-section">
        <h5 className="fw-bold mb-3">{t("faq_title")}</h5>
        <div className="faq-wrapper">
          {filteredFaq.length > 0 ? (
            filteredFaq.map((item) => (
              <div key={item.id} className="faq-item">
                <h6 className="faq-question">{item.question}</h6>
                <p className="faq-answer">{item.answer}</p>
              </div>
            ))
          ) : (
            <p className="text-center text-muted">{t("no_faq")}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default InfoPage;
