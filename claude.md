# Trading App Development Guide

## Project Overview
Real-time trading application with focus on performance, security, and data accuracy.

**Tech Stack:**
- Frontend: React 18+ with TypeScript
- State Management: Redux Toolkit + RTK Query
- UI Framework: Material-UI (MUI) or shadcn/ui
- Charts: TradingView Lightweight Charts or Recharts
- Real-time: WebSocket (Socket.io)
- Backend: Node.js/Express or Python/FastAPI
- Database: PostgreSQL with TimescaleDB extension
- Cache: Redis for session & market data

---

## Coding Standards

### TypeScript
- **Strict mode enabled** - No `any` types without explicit reason
- Define interfaces for all API responses and data models
- Use enums for order types, status codes, and market states
- Prefer type guards over type assertions

### Code Style
- Use ESLint + Prettier with Airbnb config
- Max function length: 50 lines
- Max file length: 300 lines
- Use descriptive variable names: `currentBidPrice` not `cbp`
- Comment complex calculations and business logic

### Component Structure
```
- Use functional components with hooks
- Prefer composition over inheritance
- Keep components focused (single responsibility)
- Extract reusable logic into custom hooks
- Co-locate related files (component, styles, tests)
```

### Naming Conventions
- Components: `PascalCase` (OrderBook.tsx, TradingChart.tsx)
- Hooks: `use` prefix (useMarketData, useOrderHistory)
- Utilities: `camelCase` (calculatePnL, formatCurrency)
- Constants: `UPPER_SNAKE_CASE` (MAX_ORDER_SIZE, WS_RECONNECT_DELAY)
- Types/Interfaces: `PascalCase` with descriptive names (OrderRequest, MarketTickData)

---

## Architecture & Patterns

### Application Structure
```
/src
  /components      # Reusable UI components
  /features        # Feature-based modules (orders, portfolio, charts)
  /hooks           # Custom React hooks
  /services        # API calls, WebSocket handlers
  /store           # Redux slices and store config
  /types           # TypeScript type definitions
  /utils           # Helper functions, formatters, validators
  /constants       # App-wide constants
```

### State Management
- **Redux Toolkit** for global app state (user, portfolio, orders)
- **RTK Query** for API calls and caching
- **Local component state** for UI-only state (modals, form inputs)
- **Context API** for theme, locale, user preferences
- Avoid prop drilling - use Redux for deeply nested data needs

### Real-Time Data Handling
- Use WebSocket for market data, order updates, position changes
- Implement automatic reconnection with exponential backoff
- Buffer rapid updates and batch render (debounce/throttle)
- Maintain WebSocket connection status in Redux
- Fallback to polling if WebSocket fails

### Error Handling
- Wrap all async operations in try-catch blocks
- Use error boundaries for component-level failures
- Display user-friendly error messages (never show stack traces)
- Log errors to monitoring service (Sentry, LogRocket)
- Implement retry logic for failed API calls (3 attempts max)
- Handle WebSocket disconnections gracefully

---

## Performance Best Practices

### Data Optimization
- **Virtualize long lists** (order book, trade history) using react-window
- **Memoize expensive calculations** (PnL, statistics) with useMemo
- **Debounce search/filter inputs** (300ms minimum)
- **Throttle chart updates** (max 10 updates/second)
- **Lazy load** non-critical components and routes

### Rendering Optimization
- Use React.memo for pure components that re-render frequently
- Avoid inline function definitions in render methods
- Use useCallback for event handlers passed to child components
- Batch state updates when possible
- Profile with React DevTools to identify bottlenecks

### Network Optimization
- Implement request caching with RTK Query
- Use pagination for historical data
- Compress API responses (gzip)
- Prefetch critical data on app load
- Implement stale-while-revalidate pattern

---

## Security Requirements

### Critical Rules
- **Never store sensitive data in localStorage** (use httpOnly cookies)
- **Validate all user inputs** on both client and server
- **Sanitize displayed data** to prevent XSS attacks
- **Use HTTPS only** for all communications
- **Implement rate limiting** on order submission
- **Two-factor authentication** for withdrawals and settings changes

### API Security
- Include CSRF tokens with state-changing requests
- Set short token expiration times (15 minutes)
- Implement refresh token rotation
- Use secure WebSocket connections (wss://)
- Validate JWT tokens on every request

### Data Handling
- Mask sensitive data in logs
- Never log API keys or credentials
- Encrypt sensitive data at rest
- Use environment variables for all secrets
- Implement request signing for critical operations

---

## UI/UX Best Practices

### Design Principles
- **Dark theme by default** (easier on eyes for long trading sessions)
- **High contrast** for readability (text, charts, buttons)
- **Consistent color coding**: Green (buy/profit), Red (sell/loss), Yellow (warning)
- **Responsive design**: Mobile-first approach, but optimize for desktop trading
- **Accessibility**: Proper ARIA labels, keyboard navigation support

### Performance Indicators
- Show loading states for all async operations
- Display connection status prominently (WebSocket, API)
- Provide immediate feedback for user actions (button clicks, form submissions)
- Use optimistic updates for better perceived performance
- Show latency metrics for order execution

### Data Display
- **Precision matters**: Show appropriate decimal places for each asset
- **Use tables** for structured data (orders, positions, history)
- **Real-time updates**: Highlight changed values with animations
- **Timestamps**: Always show timezone-aware timestamps
- **Empty states**: Provide helpful messages when no data available

### Form Validation
- Validate inputs in real-time (as user types)
- Disable submit buttons until form is valid
- Show clear error messages near the input field
- Prevent duplicate submissions (disable button after click)
- Confirm destructive actions (cancel orders, close positions)

---

## Trading-Specific Guidelines

### Order Management
- Validate order parameters before submission (price, quantity, type)
- Implement order confirmation for large trades (> $10K or custom threshold)
- Show estimated fees and total cost before submission
- Prevent accidental fat-finger trades (warn on unusual order sizes)
- Queue orders if WebSocket is disconnected

### Price Display
- Always show bid/ask spread clearly
- Update prices smoothly without jarring flashes
- Use appropriate precision for each trading pair
- Show price change percentage over multiple timeframes
- Highlight significant price movements

### Risk Management
- Display real-time portfolio value and P&L
- Show margin usage and available balance prominently
- Warn users approaching margin limits
- Calculate and display potential loss for open positions
- Implement circuit breakers for unusual activity

### Data Accuracy
- **Never round during calculations** - only round for display
- Use precise decimal libraries (decimal.js, big.js) for financial math
- Validate data consistency between server and client
- Implement checksums for critical data transfers
- Log discrepancies for investigation

---

## Testing Requirements

### Test Coverage
- **Minimum 80% code coverage** for business logic
- **Unit tests** for all utility functions and calculations
- **Integration tests** for API calls and WebSocket handlers
- **Component tests** for critical UI elements (order forms, charts)
- **E2E tests** for complete user flows (login → place order → view position)

### Testing Strategy
- Mock external dependencies (API, WebSocket)
- Test edge cases (zero balance, connection loss, invalid inputs)
- Test error states and recovery
- Use snapshot tests sparingly (only for stable components)
- Run tests before every commit (pre-commit hook)

### Performance Testing
- Load test with realistic data volumes (10K+ orders)
- Stress test WebSocket with rapid updates (100+ messages/second)
- Profile memory usage for long-running sessions
- Test on low-end devices and slow networks

---

## Development Workflow

### Before Starting Work
1. Pull latest changes from main branch
2. Review related code and existing patterns
3. Check feature requirements document
4. Run tests to ensure baseline functionality

### During Development
- Commit frequently with descriptive messages
- Use conventional commits: `feat:`, `fix:`, `refactor:`, etc.
- Keep PRs focused and reviewable (< 500 lines changed)
- Write tests alongside code, not after
- Update documentation for significant changes

### Before Committing
1. Run linter: `npm run lint`
2. Run tests: `npm test`
3. Build successfully: `npm run build`
4. Test in browser manually
5. Review your own changes (self-review)

### Code Review Guidelines
- Focus on logic, security, and performance
- Check for proper error handling
- Verify tests cover new functionality
- Ensure consistent code style
- Look for potential edge cases

---

## Important Notes

### Common Pitfalls
- **Floating point errors**: Use decimal libraries for financial calculations
- **Timezone issues**: Always work in UTC, convert to local only for display
- **Race conditions**: Properly handle concurrent order submissions
- **Stale data**: Implement cache invalidation strategies
- **Memory leaks**: Clean up WebSocket listeners and intervals

### Performance Bottlenecks
- Rendering large order books without virtualization
- Not throttling real-time chart updates
- Excessive re-renders due to Redux state changes
- Large bundle sizes (code split by route)
- Unoptimized images and assets

### Browser Compatibility
- Test on Chrome, Firefox, Safari, Edge
- Support last 2 major versions
- Provide graceful degradation for older browsers
- Use polyfills for missing features
- Test on both desktop and mobile browsers

---

## Monitoring & Logging

### Application Monitoring
- Track API response times and error rates
- Monitor WebSocket connection stability
- Log failed order submissions with context
- Track user actions for analytics
- Set up alerts for critical errors

### User Monitoring
- Track order submission success rate
- Monitor page load times
- Log client-side errors with stack traces
- Track WebSocket reconnection frequency
- Measure time to first trade

### What NOT to Log
- User passwords or API keys
- Full order details with amounts
- Personal identification information
- Session tokens or credentials
- Credit card or bank account numbers

---

## Environment Configuration

### Environment Variables
```
REACT_APP_API_URL=https://api.example.com
REACT_APP_WS_URL=wss://ws.example.com
REACT_APP_ENV=production
REACT_APP_ENABLE_LOGGING=false
```

### Feature Flags
- Use feature flags for gradual rollouts
- Test new features with small user percentage
- Quick rollback capability for issues
- A/B test different UI approaches

---

## Additional Resources

### Documentation
- Keep API documentation up to date
- Document complex business logic
- Maintain architecture decision records (ADRs)
- Create runbooks for common issues

### Useful Commands
```bash
npm run dev          # Start development server
npm test             # Run test suite
npm run lint         # Run ESLint
npm run build        # Production build
npm run type-check   # TypeScript type checking
```

---

## Getting Help

When encountering issues:
1. Check error logs and stack traces
2. Review relevant documentation
3. Search codebase for similar implementations
4. Consult team members or tech lead
5. Document solutions for future reference