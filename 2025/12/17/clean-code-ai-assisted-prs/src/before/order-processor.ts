// BEFORE: Messy AI-generated code
// Problems: generic names, deep nesting, mixed concerns, hidden dependencies

export function processUserOrder(data: any): any {
  const result: any = {};
  
  if (data && data.user && data.user.id) {
    const userId = data.user.id;
    const userData = getUserData(userId);
    
    if (userData && userData.orders) {
      const orders = userData.orders;
      const processedOrders: any[] = [];
      
      for (let i = 0; i < orders.length; i++) {
        const order = orders[i];
        
        if (order && order.status) {
          if (order.status === 'pending' || order.status === 'processing') {
            const orderTotal = calculateOrderTotal(order);
            const tax = orderTotal * 0.1;
            const finalTotal = orderTotal + tax;
            
            if (finalTotal > 0) {
              const processedOrder = {
                id: order.id,
                userId: userId,
                total: finalTotal,
                status: order.status,
                items: order.items || []
              };
              
              processedOrders.push(processedOrder);
            }
          }
        }
      }
      
      result.orders = processedOrders;
      result.userId = userId;
      result.count = processedOrders.length;
    } else {
      result.error = 'No orders found';
    }
  } else {
    result.error = 'Invalid user data';
  }
  
  return result;
}

function calculateOrderTotal(order: any): number {
  let total = 0;
  if (order && order.items) {
    for (const item of order.items) {
      if (item && item.price && item.quantity) {
        total += item.price * item.quantity;
      }
    }
  }
  return total;
}

// Hidden global dependency
function getUserData(userId: string): any {
  // Simulated database call
  return {
    id: userId,
    orders: [
      { id: 'order1', status: 'pending', items: [{ price: 10, quantity: 2 }] },
      { id: 'order2', status: 'completed', items: [{ price: 20, quantity: 1 }] }
    ]
  };
}
