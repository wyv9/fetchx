class CustomFooter extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        footer {
          background: rgba(0, 0, 0, 0.95);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          color: rgb(229, 229, 229);
          padding: 3rem 2rem;
          text-align: center;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.footer-content {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 2rem;
          text-align: left;
        }
        .footer-section h3 {
          color: white;
margin-bottom: 1rem;
          font-size: 1.1rem;
        }
        .footer-section ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .footer-section li {
          margin-bottom: 0.5rem;
        }
        .footer-section a {
          color: rgb(148, 163, 184);
          text-decoration: none;
          transition: color 0.2s;
        }
        .footer-section a:hover {
          color: white;
          text-decoration: underline;
}
.social-links {
          display: flex;
          gap: 1rem;
          justify-content: center;
          margin-top: 2rem;
        }
        .social-links a {
          color: rgb(148, 163, 184);
          transition: color 0.2s;
        }
        .social-links a:hover {
          color: white;
        }
.copyright {
          margin-top: 2rem;
          font-size: 0.9rem;
          color: rgb(100, 116, 139);
        }
        @media (max-width: 768px) {
          .footer-content {
            grid-template-columns: 1fr;
            text-align: center;
          }
        }
      </style>
      <footer>
        <div class="footer-content">
          <div class="footer-section">
            <h3>Project</h3>
            <ul>
              <li><a href="https://github.com/wyv9/fetchx">GitHub</a></li>
              <li><a href="https://github.com/wyv9/fetchx/releases">Releases</a></li>
              <li><a href="https://github.com/wyv9/fetchx/issues">Issues</a></li>
            </ul>
          </div>
          <div class="footer-section">
            <h3>Documentation</h3>
            <ul>
              <li><a href="https://github.com/wyv9/fetchx/blob/main/README.md">README</a></li>
            </ul>
          </div>
          <div class="footer-section">
            <h3>Legal</h3>
            <ul>
              <li><a href="https://github.com/wyv9/fetchx/blob/main/LICENSE">License</a></li>
            </ul>
          </div>
</div>
        <div class="social-links">
          <a href="#github"><i data-feather="github"></i></a>
        </div>
        <div class="copyright">
          &copy; 2025 FetchX. All rights reserved. \n Made with love by wyv <3
        </div>
      </footer>
    `;
  }
}

customElements.define('custom-footer', CustomFooter);
