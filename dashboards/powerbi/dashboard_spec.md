# Power BI Dashboard Specification

Power BI Desktop is required to build the final `.pbix` from these source files.

## Pages
- Executive Overview
- Revenue Analytics
- Subscription Analytics
- Customer Analytics
- Retention Analytics
- Growth Analytics

## Required Features

- Advanced DAX measures documented in `measures.dax`
- Time intelligence page filters
- Drill-through target pages
- Bookmarks for executive and detailed views
- Custom tooltips for KPI context
- Field parameters for metric switching
- Forecasting visuals on trend pages

## Source Tables

Import every CSV from `data/cleaned` and follow the ER diagram in `architecture/er_diagram.md`.
