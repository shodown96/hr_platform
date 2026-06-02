# ============================================================================
# EVENT-DRIVEN ARCHITECTURE - BEST PRACTICES FOR HR SYSTEM
# ============================================================================

"""
GOLDEN RULE: Each service owns its data, broadcasts changes, reacts to others' changes

ARCHITECTURE PRINCIPLES:
========================

1. SINGLE SOURCE OF TRUTH
   - Auth Service owns: Users, Roles, Permissions
   - Employee Service owns: Employees, Departments, Positions  
   - Payroll Service owns: Salaries, Payroll Records

2. EVENT PUBLISHING
   - Services publish events when THEIR data changes
   - Events are facts: "X happened" not commands: "Do Y"
   
3. EVENT CONSUMPTION
   - Services subscribe to events about data they depend on
   - Each service decides how to react (invalidate cache, update copy, etc.)

4. CACHE STRATEGY
   - INVALIDATE on change (don't update)
   - Force re-fetch from source on next request
   - This ensures eventual consistency and simplicity
"""


# ============================================================================
# EVENT CATALOG - WHAT MESSAGES TO SEND
# ============================================================================

"""
════════════════════════════════════════════════════════════════════════
AUTH SERVICE EVENTS (Published by Auth Service)
════════════════════════════════════════════════════════════════════════

Event: user.created ✅
When: New user account created
Data: {user_id, email}
Consumers: None currently subscribed

Event: user.role.assigned ✅
When: Role assigned to user
Data: {user_id, role_id, role_name}
Consumers: Employee Service, Payroll Service (invalidate permission cache)

Event: user.role.removed ✅
When: Role removed from user
Data: {user_id, role_id, role_name}
Consumers: Employee Service, Payroll Service (invalidate permission cache)

Event: user.permission.granted ✅
When: Permission directly granted to user
Data: {user_id, permission_id, permission_name}
Consumers: Employee Service, Payroll Service (invalidate permission cache)

Event: user.permission.removed ✅
When: Permission directly revoked from user
Data: {user_id, permission_id, permission_name}
Consumers: Employee Service, Payroll Service (invalidate permission cache)

Event: user.deactivated ✅
When: User account deactivated
Data: {user_id}
Consumers: Employee Service, Payroll Service (block access, invalidate cache)

Event: user.password.changed ✅
When: User changed their password
Data: {user_id}
Consumers: Audit Service (not yet implemented)

Event: user.password.reset ✅
When: User reset their password via OTP
Data: {user_id}
Consumers: Audit Service (not yet implemented)


════════════════════════════════════════════════════════════════════════
EMPLOYEE SERVICE EVENTS (Published by Employee Service)
════════════════════════════════════════════════════════════════════════

Event: employee.created ✅
When: New employee record created
Data: {employee_id, user_id, employee_code, employee_email, first_name, last_name, hire_date, department_id, position_id}
Consumers:
  - Auth Service: No action (user account already exists)
  - Payroll Service: Creates $0 salary placeholder at hire date

Event: employee.updated ✅
When: Employee details updated
Data: {employee_id, user_id, employee_code, employee_email, updated_fields{}}
Consumers:
  - Auth Service: Syncs email on the user account if email changed
  - Payroll Service: Flags salary for review if department_id or position_id changed

Event: employee.terminated ✅
When: Employee terminated
Data: {employee_id, user_id, employee_code, employee_email, termination_date, reason}
Consumers:
  - Auth Service: Sets user.is_active = false
  - Payroll Service: Deactivates salary, creates prorated final payroll record

Event: employee.department.changed ✅
When: Employee moves to a different department
Data: {employee_id, user_id, employee_code, employee_email, department_id, department_name, effective_date}
Consumers:
  - Auth Service: Clears permission cache if effective_date <= today
  - Payroll Service: Versions salary (carries forward at same rate) if effective_date <= today

Event: employee.position.changed ✅
When: Employee promoted or demoted
Data: {employee_id, user_id, employee_code, employee_email, position_id, position_name, effective_date}
Consumers:
  - Auth Service: Clears permission cache if effective_date <= today
  - Payroll Service: Versions salary (carries forward at same rate) if effective_date <= today


════════════════════════════════════════════════════════════════════════
PAYROLL SERVICE EVENTS (Published by Payroll Service)
════════════════════════════════════════════════════════════════════════

Event: salary.created ✅
When: Salary set for employee
Data: {employee_id, basic_salary, currency, payment_frequency, effective_from}
Consumers:
  - Finance Service: Budget tracking (not yet implemented)

Event: salary.changed ✅
When: Salary adjusted
Data: {employee_id, basic_salary, currency, payment_frequency, effective_from}
Consumers:
  - Finance Service: Update budget (not yet implemented)
  - Audit Service: Log for compliance (not yet implemented)

Event: payroll.processed ✅
When: Payroll record marked as paid
Data: {payroll_id, employee_id, pay_period_start, pay_period_end, gross_salary, net_salary}
Consumers:
  - Finance Service: Accounting integration (not yet implemented)
  - Banking Service: Initiate payment transfer (not yet implemented)

Event: payroll.failed ✅
When: Payroll processing failed
Data: {payroll_id, employee_id, error_reason}
Consumers:
  - Notification Service: Alert HR/Finance (not yet implemented)
"""


# ============================================================================
# CACHE STRATEGY - INVALIDATE VS UPDATE
# ============================================================================

"""
QUESTION: When permissions change, should we INVALIDATE or UPDATE cache?

RECOMMENDATION: ALWAYS INVALIDATE (Don't Update)

WHY INVALIDATE?
✅ Simpler implementation
✅ No complex cache synchronization
✅ Guarantees consistency (fetch from source)
✅ Handles race conditions naturally
✅ Works with partial failures

WHY NOT UPDATE?
❌ Complex - need to recalculate aggregated permissions
❌ Race conditions - what if multiple updates?
❌ Partial failures - what if update fails mid-way?
❌ Cache becomes source of truth (violates single source principle)


FLOW EXAMPLE:
=============

1. Admin removes "employee:write" from Alice's role
   ↓
2. Auth Service publishes: user.role.removed
   ↓
3. Employee Service receives event
   ↓
4. Employee Service INVALIDATES Alice's permission cache
   (Does NOT try to update it)
   ↓
5. Alice's next request to Employee Service
   ↓
6. Cache miss → Employee Service checks JWT
   ↓
7. JWT still has old permissions (not expired yet)
   ↓
8. Employee Service calls Auth Service: "What are Alice's current permissions?"
   (Optional: could force re-login instead)
   ↓
9. Auth Service returns fresh permissions
   ↓
10. Employee Service caches NEW permissions
    ↓
✅ Alice now has correct permissions
"""


# ============================================================================
# IMPLEMENTATION: CACHE INVALIDATION
# ============================================================================

# Employee Service: dependencies/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from hr_shared.auth.jwt_utils import JWTManager, TokenData
from shared.cache.permissions import get_permission_cache, PermissionCache
from clients.auth_client import AuthServiceClient
from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.AUTH_SERVICE_URL}/api/v1/auth/sign-in")
jwt_manager = JWTManager(secret_key=settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    cache: PermissionCache = Depends(get_permission_cache)
) -> TokenData:
    """
    Validate JWT and get permissions
    
    STRATEGY:
    1. Validate JWT signature
    2. Check cache for permissions
    3. If cache miss, fetch from Auth Service
    4. Cache the fresh permissions
    """
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Validate token
    token_data = jwt_manager.verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    # Check if token expired
    if token_data.exp and token_data.exp < datetime.utcnow():
        raise credentials_exception
    
    # Try to get permissions from cache
    cached_permissions = await cache.get_user_permissions(token_data.user_id)
    
    if cached_permissions is not None:
        # Cache hit - use cached permissions
        token_data.permissions = cached_permissions
        print(f"✅ Cache hit for user {token_data.user_id}")
    else:
        # Cache miss - fetch from Auth Service
        print(f"❌ Cache miss for user {token_data.user_id} - fetching from Auth Service")
        
        auth_client = AuthServiceClient(settings.AUTH_SERVICE_URL)
        try:
            fresh_permissions = await auth_client.get_user_permissions(
                token_data.user_id,
                token
            )
            token_data.permissions = fresh_permissions
            
            # Cache the fresh permissions
            await cache.set_user_permissions(
                token_data.user_id,
                fresh_permissions,
                ttl=timedelta(minutes=15)  # Cache for 15 minutes
            )
            print(f"✅ Cached fresh permissions for user {token_data.user_id}")
        except Exception as e:
            # Fallback to JWT permissions if Auth Service unavailable
            print(f"⚠️ Auth Service unavailable, using JWT permissions: {e}")
            # Keep permissions from JWT token
    
    return token_data


# ============================================================================
# AUTH SERVICE: Permission Fetch Endpoint
# ============================================================================

# Auth Service: routes/auth.py

@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user_from_token)
):
    """
    Get current permissions for a user
    Other services call this when cache misses
    """
    
    # Only allow users to fetch their own permissions or admins
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's permissions"
        )
    
    permissions = await AuthService.get_user_permissions(db, user_id)
    
    return {
        "user_id": user_id,
        "permissions": permissions,
        "fetched_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# AUTH CLIENT (clients/auth_client.py)
# ============================================================================

import httpx
from typing import List


class AuthServiceClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
    
    async def get_user_permissions(
        self,
        user_id: str,
        auth_token: str
    ) -> List[str]:
        """Fetch user's current permissions from Auth Service"""
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/auth/users/{user_id}/permissions",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            response.raise_for_status()
            data = response.json()
            return data["permissions"]


# ============================================================================
# EVENT HANDLER: Permission Changes
# ============================================================================

# Employee Service: messaging/auth_event_consumer.py

class AuthEventConsumer:
    
    async def handle_role_changed(self, event_data: dict):
        """
        Handle role assignment/removal
        
        STRATEGY:
        1. Invalidate cache only
        2. Don't try to update permissions
        3. Let next request fetch fresh data
        """
        user_id = event_data["user_id"]
        role_name = event_data["role_name"]
        event_type = event_data["event_type"]
        
        print(f"🔄 Role '{role_name}' {event_type} for user {user_id}")
        
        # INVALIDATE cache (don't update)
        cache = await get_permission_cache()
        await cache.invalidate_all_for_user(user_id)
        
        print(f"✅ Cache invalidated for user {user_id}")
        print(f"   Next request will fetch fresh permissions from Auth Service")


# ============================================================================
# COMPLETE EVENT FLOWS
# ============================================================================

"""
════════════════════════════════════════════════════════════════════════
FLOW 1: EMPLOYEE TERMINATION
════════════════════════════════════════════════════════════════════════

1. HR terminates employee in Employee Service
   POST /api/v1/employees/{id}/terminate
   
2. Employee Service:
   ✅ Updates employee.employment_status = "terminated"
   ✅ Sets employee.termination_date
   ✅ Publishes event: employee.terminated
   
3. Auth Service receives employee.terminated:
   ✅ Deactivates user (user.is_active = False)
   ✅ Publishes event: user.deactivated
   
4. Payroll Service receives employee.terminated:
   ✅ Deactivates salary (effective_to = termination_date)
   ✅ Cancels future pending payrolls
   ✅ Flags need for final payroll calculation
   
5. All Services receive user.deactivated:
   ✅ Invalidate all caches for this user
   ✅ User's current sessions remain valid until JWT expires
   ✅ New requests will fail (user.is_active = False check)

RESULT:
- Employee data updated
- User account disabled
- Salary stopped
- All caches cleared
- System consistent across all services


════════════════════════════════════════════════════════════════════════
FLOW 2: SALARY CHANGE
════════════════════════════════════════════════════════════════════════

1. HR updates salary in Payroll Service
   POST /api/v1/payroll/salaries
   
2. Payroll Service:
   ✅ Deactivates old salary record
   ✅ Creates new salary record
   ✅ Publishes event: salary.changed
   
3. Finance Service receives salary.changed:
   ✅ Updates budget forecasts
   ✅ Recalculates departmental costs
   
4. Audit Service receives salary.changed:
   ✅ Logs change for compliance
   ✅ Checks if approval was required

RESULT:
- Salary updated in Payroll Service
- Budget updated in Finance Service  
- Audit trail created
- No cache invalidation needed (salary not cached)


════════════════════════════════════════════════════════════════════════
FLOW 3: PERMISSION CHANGE
════════════════════════════════════════════════════════════════════════

1. Admin removes role from user in Auth Service
   DELETE /api/v1/auth/users/{user_id}/roles/{role_id}
   
2. Auth Service:
   ✅ Removes UserRole record
   ✅ Publishes event: user.role.removed
   
3. All Services receive user.role.removed:
   ✅ Invalidate permission cache for user_id
   (Do NOT try to update cache)
   
4. User makes next request to Employee Service:
   ✅ Cache miss (was invalidated)
   ✅ Employee Service calls Auth Service
   ✅ Gets fresh permissions
   ✅ Caches for 15 minutes
   
5. User tries to access removed permission:
   ❌ 403 Forbidden

RESULT:
- Permission change takes effect within 15 minutes (cache TTL)
- Or immediately on cache invalidation
- All services eventually consistent
"""


# ============================================================================
# SCALABILITY CONSIDERATIONS
# ============================================================================

"""
CACHE TTL STRATEGY:
==================

Short TTL (5-15 minutes):
✅ Changes take effect quickly
✅ Reduces stale cache issues
❌ More calls to Auth Service

Long TTL (1-24 hours):
✅ Fewer calls to Auth Service
✅ Better performance
❌ Changes take longer to propagate


RECOMMENDATION: 15 minutes
- Good balance between consistency and performance
- Critical changes (termination, deactivation) invalidate immediately
- Normal changes (role assignment) propagate within 15 min


REDIS EVICTION POLICY:
=====================

Set Redis with LRU eviction:
- maxmemory-policy: allkeys-lru
- maxmemory: 2gb

This ensures:
✅ Most active users stay cached
✅ Inactive users automatically evicted
✅ No manual cleanup needed


EVENT ORDERING:
==============

Problem: Events might arrive out of order

Solution: Include timestamp in events
- Consumer checks timestamp
- Ignores events older than current state


IDEMPOTENCY:
===========

Problem: Events might be delivered twice

Solution: Track processed event IDs
- Store event_id in Redis with TTL
- Skip if event_id already processed


CIRCUIT BREAKER:
===============

Problem: Auth Service might be down

Solution: Fallback to JWT permissions
- If Auth Service unavailable
- Use permissions from JWT token
- Log warning
- Retry later
"""


# ============================================================================
# MONITORING & OBSERVABILITY
# ============================================================================

"""
KEY METRICS TO TRACK:
====================

1. Cache Hit Rate:
   - Target: >80%
   - Low hit rate = TTL too short or too many invalidations

2. Event Processing Lag:
   - Target: <1 second
   - High lag = consumer falling behind

3. Auth Service Call Rate:
   - Target: <100/sec
   - High rate = cache not working

4. Failed Event Processing:
   - Target: 0
   - Any failures need investigation


LOGGING BEST PRACTICES:
======================

Log all cache operations:
✅ Cache hit/miss
✅ Cache invalidation
✅ Fresh permission fetch

Log all events:
✅ Event published
✅ Event received
✅ Event processed
✅ Event failed


ALERTS:
======

Alert on:
⚠️ Cache hit rate <70%
⚠️ Event processing lag >5 seconds
⚠️ Failed events >10/hour
⚠️ Auth Service unavailable
"""


# ============================================================================
# SUMMARY: RECOMMENDED EVENT ARCHITECTURE
# ============================================================================

"""
✅ DO:
- Publish events when YOUR data changes
- Invalidate caches, don't update them
- Fetch fresh data from source on cache miss
- Include timestamps in events
- Make consumers idempotent
- Log everything
- Monitor cache hit rates

❌ DON'T:
- Try to update cached permissions from events
- Make synchronous calls between services
- Let services directly access other services' databases
- Publish events for every field change (batch if possible)
- Forget to handle Auth Service being down
- Cache permissions forever (use 15-min TTL)


ARCHITECTURE BENEFITS:
=====================

✅ Scalable: Each service independent
✅ Resilient: Services work even if others down
✅ Consistent: Single source of truth
✅ Maintainable: Clear ownership
✅ Debuggable: Event log shows what happened
✅ Testable: Can test services in isolation
"""