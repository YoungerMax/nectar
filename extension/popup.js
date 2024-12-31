class PublicSuffixList {
    constructor(rules) {
        // Split rules into normal rules and exception rules
        this.rules = [];
        this.exceptionRules = [];

        rules.split('\n').forEach(line => {
            // Remove comments and whitespace
            const rule = line.split(/\s/)[0].trim().toLowerCase();

            // Skip empty lines and comments
            if (!rule || rule.startsWith('//')) {
                return;
            }

            // Handle exception rules
            if (rule.startsWith('!')) {
                this.exceptionRules.push(rule.slice(1));
            } else {
                this.rules.push(rule);
            }
        });

        // Sort rules by number of labels (descending)
        this.rules.sort((a, b) => b.split('.').length - a.split('.').length);
        this.exceptionRules.sort((a, b) => b.split('.').length - a.split('.').length);
    }

    /**
     * Check if a domain matches a rule according to PSL matching algorithm
     */
    matchesRule(domain, rule) {
        const domainLabels = domain.split('.');
        const ruleLabels = rule.split('.');

        // Domain must have at least as many labels as the rule
        if (domainLabels.length < ruleLabels.length) {
            return false;
        }

        // Check labels from right to left
        for (let i = 1; i <= ruleLabels.length; i++) {
            const domainLabel = domainLabels[domainLabels.length - i];
            const ruleLabel = ruleLabels[ruleLabels.length - i];

            if (ruleLabel !== '*' && ruleLabel !== domainLabel) {
                return false;
            }
        }

        return true;
    }

    /**
     * Get the public suffix for a domain
     */
    getPublicSuffix(domain) {
        domain = domain.toLowerCase();

        // Find all matching rules
        const matchingRules = this.rules.filter(rule => this.matchesRule(domain, rule));
        const matchingExceptions = this.exceptionRules.filter(rule =>
            this.matchesRule(domain, rule)
        );

        // If no rules match, use "*"
        if (matchingRules.length === 0 && matchingExceptions.length === 0) {
            const labels = domain.split('.');
            return labels[labels.length - 1];
        }

        // If there's a matching exception rule, use it
        if (matchingExceptions.length > 0) {
            const rule = matchingExceptions[0];
            const ruleLabels = rule.split('.');
            return ruleLabels.slice(1).join('.');
        }

        // Otherwise use the rule with the most labels
        const prevailingRule = matchingRules[0];
        const domainLabels = domain.split('.');
        const ruleLabels = prevailingRule.split('.');
        return domainLabels.slice(-ruleLabels.length).join('.');
    }

    /**
     * Get the registrable domain (public suffix plus one label)
     */
    getRegistrableDomain(domain) {
        const publicSuffix = this.getPublicSuffix(domain);
        const labels = domain.split('.');
        const publicSuffixLabels = publicSuffix.split('.');

        if (labels.length <= publicSuffixLabels.length) {
            return null;
        }

        const registrableLabels = labels.slice(-(publicSuffixLabels.length + 1));
        return registrableLabels.join('.');
    }
}

const HOST = 'http://127.0.0.1:8000/coupons_data';

async function getPublicSuffixListInstance() {
    const psl = await fetch('https://publicsuffix.org/list/public_suffix_list.dat');
    const pslText = await psl.text();
    
    return new PublicSuffixList(pslText);
}

async function getCurrentTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function fetchCoupons() {
    document.getElementById('app').innerHTML = `Loading...`;

    new Promise(async (resolve, reject) => {
        try {
            const psl = await getPublicSuffixListInstance();
            const tab = await getCurrentTab();
            const url = new URL(tab.url);
            const domain = url.hostname;
            const rootDomain = psl.getRegistrableDomain(domain);
            const response = await fetch(`${HOST}/${rootDomain}.json`);
    
            if (response.ok) {
                const coupons = await response.json();
                const now = new Date();
    
                const validCoupons = coupons
                    .filter(coupon => new Date(coupon.expiry) > now)
                    .sort((a, b) => new Date(b.expiry) - new Date(a.expiry));
    
                const html = validCoupons.map(coupon => `
              <div class="coupon">
                <strong>${coupon.title}</strong>
                ${coupon.description ? `<p>${coupon.description}</p>` : ''}
                <div>Code: <span class="code">${coupon.code}</span></div>
                <div class="expiry">Expires: ${formatDate(coupon.expiry)}</div>
              </div>
            `).join('');
    
                document.getElementById('app').innerHTML = `<h1>${coupons.length} coupons found</h1>${html}`;
            } else if (response.status === 404) {
                document.getElementById('app').innerHTML = `<h1>No coupons found</h1><p>If you have a coupon, please add it on our GitHub!</p>`;
            } else {
                throw new Error('Failed to fetch coupons: ' + response.status);
            }
        } catch (error) {
            document.getElementById('app').innerHTML = `
          <div class="error">
            <p>Failed to load coupons</p>
            <p>${error.message}</p>
          </div>
        `;
        }

        resolve();
    }).then();

}

document.addEventListener('DOMContentLoaded', fetchCoupons);