/**
 * RainSense Farmer - AI Farming Advisory & Insights Renderer
 */

class InsightsRenderer {
  renderAdvisory(containerId, insightData = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const headline = insightData.headline || "Atmospheric conditions monitored.";
    const bullets = insightData.advisory_bullet_points || [];
    const irrigation = insightData.irrigation_advice || "Check soil moisture before irrigating.";
    const spraying = insightData.spraying_advice || "Favorable conditions for spraying if wind is calm.";
    const waterlogging = insightData.waterlogging_advisory || "Low waterlogging risk.";
    const confidence = insightData.confidence_pct || 80;
    const factors = insightData.key_factors || [];

    container.innerHTML = `
      <div style="background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%); border-radius: var(--radius-lg); padding: 1.25rem; border: 1px solid #bbf7d0;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 0.85rem;">
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 800; color: #166534; line-height: 1.3;">
              🤖 ${headline}
            </h3>
            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">
              Decision support synthesized from 15 km rainfall radar, soil saturation, and local forecasts.
            </p>
          </div>
          <div style="text-align: right; flex-shrink: 0;">
            <span style="font-size: 0.7rem; font-weight: 700; color: #15803d; text-transform: uppercase;">Confidence</span>
            <div style="font-size: 1.3rem; font-weight: 800; color: #166534;">${confidence}%</div>
          </div>
        </div>

        <!-- 3 Pillars of Farming Decision -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.85rem; margin-top: 1rem;">
          <!-- Irrigation Pillar -->
          <div style="background: #ffffff; padding: 0.85rem; border-radius: var(--radius-md); border: 1px solid var(--border-color); box-shadow: var(--shadow-sm);">
            <div style="display: flex; align-items: center; gap: 0.4rem; font-weight: 700; font-size: 0.9rem; color: #0284c7; margin-bottom: 0.35rem;">
              💧 Irrigation Decision
            </div>
            <p style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.4;">
              ${irrigation}
            </p>
          </div>

          <!-- Spraying Pillar -->
          <div style="background: #ffffff; padding: 0.85rem; border-radius: var(--radius-md); border: 1px solid var(--border-color); box-shadow: var(--shadow-sm);">
            <div style="display: flex; align-items: center; gap: 0.4rem; font-weight: 700; font-size: 0.9rem; color: #d97706; margin-bottom: 0.35rem;">
              🌿 Spraying & Chemicals
            </div>
            <p style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.4;">
              ${spraying}
            </p>
          </div>

          <!-- Drainage Pillar -->
          <div style="background: #ffffff; padding: 0.85rem; border-radius: var(--radius-md); border: 1px solid var(--border-color); box-shadow: var(--shadow-sm);">
            <div style="display: flex; align-items: center; gap: 0.4rem; font-weight: 700; font-size: 0.9rem; color: #10b981; margin-bottom: 0.35rem;">
              🚜 Soil Drainage & Bunds
            </div>
            <p style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.4;">
              ${waterlogging}
            </p>
          </div>
        </div>

        <!-- Key Contributing Factors -->
        ${factors.length > 0 ? `
        <div style="margin-top: 1rem; padding-top: 0.85rem; border-top: 1px dashed #bbf7d0; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
          <span style="font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Top Factors:</span>
          ${factors.map(f => `
            <span style="font-size: 0.75rem; background: #e2e8f0; color: #334155; padding: 0.2rem 0.55rem; border-radius: var(--radius-full); font-weight: 600;">
              • ${f}
            </span>
          `).join('')}
        </div>` : ''}
      </div>
    `;
  }
}

window.insightsRenderer = new InsightsRenderer();
