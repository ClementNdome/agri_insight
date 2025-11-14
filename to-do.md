1. **Project Setup and Restructuring**:
   - Rename the project from "forest_monitoring" to "agri_insight" to better align with the agriculture focus. Update all references in settings.py, urls.py, wsgi.py, and other config files.
   - Review and tweak the existing implementation: Adapt models (e.g., AreaOfInterest to include agriculture-specific fields like crop_type as a CharField with choices for common crops such as 'wheat', 'corn', 'rice'), VegetationIndex to include ag-relevant indices (e.g., EVI, LAI in addition to NDVI), and MonitoringData to incorporate yield prediction fields (e.g., predicted_yield as FloatField).
   - Ensure the project adheres to PEP 8 coding standards: Use black or autopep8 to format all Python files, including views.py and admin.py.
   - Set up a virtual environment if not already done, and create a requirements.txt with pinned versions (e.g., Django==5.1, djangorestframework==3.15, geopandas==1.0, rasterio==1.4, tensorflow==2.17 for AI features).
   - Configure environment variables properly: Expand .env to include separate keys for development, testing, and production (e.g., DEBUG, DATABASE_URL using dj-database-url for portability).
   - Integrate version control best practices: Initialize Git if not present, create .gitignore for ignoring __pycache__, .env, media/, staticfiles/, and add initial commit with the current blueprint.
   - Set up testing framework: Install pytest and pytest-django, create a tests/ directory with unit tests for models (e.g., test AreaOfInterest geometry validation) and views (e.g., test calculate action returns correct status).
   - Enable CI/CD stubs: Add a .github/workflows/ directory with a basic YAML for GitHub Actions to run tests and linting on push.

2. **Authentication System Overhaul**:
   - Implement user signup and login using Django's built-in auth with custom forms: Create accounts/ app if not exists, with models extending AbstractUser (add fields like is_farmer as BooleanField).
   - Develop signup page: Use Class-Based Views (CBV) in accounts/views.py for SignupView (inherit from CreateView), with a template accounts/signup.html using Bootstrap 5 for modern styling (include fields: username, email, password, confirm_password, crop_interests as MultipleChoiceField).
   - Develop login page: Use LoginView in accounts/views.py, template accounts/login.html with Bootstrap, add "Remember Me" checkbox and password reset link.
   - Add email verification: Integrate django-allauth for social logins (Google, optionally) and email confirmation on signup.
   - Secure authentication: Enforce HTTPS in production (SECURE_SSL_REDIRECT=True in settings.py), use argon2 password hasher, and add rate limiting with django-ratelimit.
   - Tweak current user handling: Update get_queryset in views.py to strictly enforce IsAuthenticated, remove anonymous user fallback, and integrate with existing created_by fields in models.

3. **Landing Page Development**:
   - Create a post-login landing page: In monitoring/views.py, add a LandingView (TemplateView) that redirects from login success URL, template monitoring/landing.html.
   - Make it intuitive and detailed: Use Bootstrap grid for layout, include sections like: Welcome message personalized with user.name, quick stats (e.g., number of farms monitored via MonitoringData count), recent alerts (list from MonitoringAlert), and calibrated widgets (e.g., a carousel of educational tips on sustainable farming pulled from a new Tips model).
   - Add calibration elements: Include a customizable user profile section (edit bio, preferences for units like hectares vs. acres), and a getting-started guide with step-by-step cards linking to dashboard.
   - Ensure responsiveness: Use media queries in CSS for mobile, test with Bootstrap's responsive classes.
   - Integrate with existing: Pull data from user's AreaOfInterest queryset for personalized content.

4. **Dashboard Page Development**:
   - Build the core dashboard: Create DashboardView in monitoring/views.py (LoginRequiredMixin, TemplateView), template monitoring/dashboard.html.
   - Implement area drawing: Use Leaflet.js with Draw plugin (add to STATICFILES_DIRS), allow users to draw polygons on the map, convert to GeoJSON, and POST to create_from_geojson action (tweak to handle drawn features).
   - Add index selection and calculation: Dropdown for VegetationIndex (populate from API), date range picker (using Bootstrap-datepicker), satellite selector (e.g., Sentinel-2, Landsat), trigger calculate action via AJAX (use jQuery for async calls).
   - Return results on basemap: After calculation, overlay results as styled layers on Leaflet map, mimicking Google Earth Engine: Use color ramps (e.g., viridis for NDVI: low red, high green via Leaflet.ImageOverlay or GeoJSON layers with style functions based on mean_value).
   - Style results like GEE: Implement legend control (Leaflet.legend), time slider for historical data (using Leaflet.TimeDimension if needed), and zoom-to-fit on area.
   - Add advanced spatial features: Buffer analysis (use geopandas in a new service to create buffered geometry, save as new AreaOfInterest), intersection with external layers (e.g., soil maps from USDA API), spatial queries (e.g., find overlapping farms).
   - Add advanced non-spatial features: AI yield predictions (integrate TensorFlow in VegetationIndexCalculator to train/use a simple model on historical MonitoringData), report generation (export to PDF with weasyprint, including charts via matplotlib), email/SMS alerts (use django-celery-email and twilio).
   - Ensure intuitiveness: Use modals for forms, tooltips for explanations, and real-time updates via WebSockets (add channels for async notifications).
   - Tweak existing: Enhance monitoring_data and alerts actions to return GeoJSON for map overlays, integrate map_html from calculate into dashboard.

5. **Admin Interface Revamp**:
   - Install and configure a modern admin theme: Use django-admin-interface (or django-jazzmin as of 2025 trends for customizable themes), add to INSTALLED_APPS, configure in settings.py with ADMIN_INTERFACE_THEME = {'theme': 'dark-modern'}.
   - Customize admin.py: For each model, add custom list_display with icons (using font-awesome), inline forms (e.g., MonitoringData inline in AreaOfInterestAdmin), and custom change forms with tabs (using admin.TabularInline).
   - Make it stylish and professional: Override admin templates (extend base_site.html with custom CSS for gradients, shadows), add dashboard widgets (e.g., recent alerts chart using Chart.js).
   - Enhance functionality: Add export actions (to CSV/Excel via django-import-export), custom filters (e.g., by crop_type), and permissions (e.g., farmer users see read-only admin).
   - Tweak existing admin registrations: Update fieldsets for better organization, add search_fields for all models, and ensure GIS widgets are styled with modern map providers (e.g., switch to OpenStreetMap tiles).

6. **Backend Core Files Overhaul**:
   - Refactor views.py: Split into multiple files (e.g., areas.py, monitoring.py) under monitoring/views/, use CBVs where possible (e.g., convert ViewSets to generics if simpler), add docstrings and type hints (using mypy for static typing).
   - Update models.py (assuming exists): Add validators (e.g., MinValueValidator for thresholds), indexes for frequent queries (e.g., GIST index on geometry), and signals (e.g., post_save to trigger alerts).
   - Enhance services.py (e.g., VegetationIndexCalculator): Modularize into methods (e.g., fetch_data, compute_index, generate_map), add error handling with custom exceptions, integrate AI (e.g., scikit-learn for anomaly detection in indices).
   - Best practices: Use DRY principle (extract common code to mixins), secure APIs (add API keys with drf-yasg for Swagger docs), optimize queries (use select_related/prefetch_related in get_queryset).
   - Settings.py tweaks: Enable CORS fully, set DEFAULT_PERMISSION_CLASSES to IsAuthenticated, add SENTRY_SDK for error tracking, configure STATICFILES_STORAGE for production (e.g., whitenoise).
   - Add new apps/files: Create utils/ for helpers (e.g., geo_utils.py for spatial ops), api/ for DRF routers, and tasks.py for Celery tasks (e.g., periodic monitoring).

7. **Project Cleanup and Optimization**:
   - Delete unnecessary files: Remove any unused templates (e.g., if index.html is basic, replace with landing.html), commented-out middleware (enable if needed), redundant models or views (e.g., if SatelliteImage is underused, merge into MonitoringData).
   - Clean structure: Organize into apps (monitoring for core, accounts for auth), use manage.py startapp for new ones, ensure migrations are applied and squashed.
   - Performance tweaks: Add caching (django-redis for querysets), database indexing, and profiling (use django-silk for request analysis).
   - Security audit: Run django-check or bandit for vulnerabilities, ensure CSRF protection on all forms.
   - Documentation: Add README.md with setup instructions, API docs via drf-spectacular, and inline comments in code.

8. **Integration and Testing**:
   - Tweak GEE integration: In services, add retry logic for API calls (using tenacity), optimize for ag (e.g., filter collections for crop seasons), handle quotas with user limits.
   - End-to-end testing: Use Selenium for browser tests on dashboard (e.g., draw area, calculate, verify map overlay).
   