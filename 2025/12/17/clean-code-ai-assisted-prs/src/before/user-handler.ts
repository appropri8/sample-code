// BEFORE: Generic handler pattern with nested conditionals
// Problems: generic name, deep nesting, mixed validation and processing

export function handleUserRequest(data: any): any {
  if (data) {
    if (data.userId) {
      if (data.action) {
        if (data.action === 'getOrders') {
          if (data.userId.length > 0) {
            const orders = getUserOrders(data.userId);
            if (orders) {
              if (orders.length > 0) {
                return {
                  success: true,
                  data: orders
                };
              } else {
                return {
                  success: false,
                  error: 'No orders found'
                };
              }
            } else {
              return {
                success: false,
                error: 'Failed to fetch orders'
              };
            }
          } else {
            return {
              success: false,
              error: 'Invalid user ID'
            };
          }
        } else if (data.action === 'getProfile') {
          const profile = getUserProfile(data.userId);
          if (profile) {
            return {
              success: true,
              data: profile
            };
          } else {
            return {
              success: false,
              error: 'Profile not found'
            };
          }
        } else {
          return {
            success: false,
            error: 'Unknown action'
          };
        }
      } else {
        return {
          success: false,
          error: 'Action is required'
        };
      }
    } else {
      return {
        success: false,
        error: 'User ID is required'
      };
    }
  } else {
    return {
      success: false,
      error: 'Request data is required'
    };
  }
}

function getUserOrders(userId: string): any[] | null {
  // Simulated database call
  return [
    { id: 'order1', total: 100 },
    { id: 'order2', total: 200 }
  ];
}

function getUserProfile(userId: string): any | null {
  // Simulated database call
  return {
    id: userId,
    name: 'John Doe',
    email: 'john@example.com'
  };
}
