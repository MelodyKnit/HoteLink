# HoteLink API 路由清单（源码自动生成）

- 生成时间：2026-04-13 21:49:06
- 来源文件：`backend/apps/api/urls.py` + `backend/apps/api/views.py`
- 总路由数：**103**

> 本文件由 `scripts/docs/generate_api_inventory.py` 生成，请勿手工编辑。

## Root

| Method | Path | View | Name |
|---|---|---|---|
| `GET` | `/api/v1/` | `ApiRootView` | `api-root` |

## System

| Method | Path | View | Name |
|---|---|---|---|
| `GET` | `/api/v1/system/init-check` | `SystemInitCheckView` | `system-init-check` |
| `POST` | `/api/v1/system/init-setup` | `SystemInitSetupView` | `system-init-setup` |

## Common

| Method | Path | View | Name |
|---|---|---|---|
| `GET` | `/api/v1/common/cities` | `CommonCitiesView` | `common-cities` |
| `GET` | `/api/v1/common/dicts` | `CommonDictsView` | `common-dicts` |
| `GET` | `/api/v1/common/image-thumb` | `CommonImageThumbView` | `common-image-thumb` |
| `POST` | `/api/v1/common/upload` | `CommonUploadView` | `common-upload` |

## Public

| Method | Path | View | Name |
|---|---|---|---|
| `POST` | `/api/v1/public/auth/admin-login` | `AdminLoginView` | `public-admin-login` |
| `POST` | `/api/v1/public/auth/login` | `UserLoginView` | `public-login` |
| `POST` | `/api/v1/public/auth/refresh` | `RefreshTokenApiView` | `public-refresh` |
| `POST` | `/api/v1/public/auth/register` | `UserRegisterView` | `public-register` |
| `GET` | `/api/v1/public/home` | `PublicHomeView` | `public-home` |
| `GET` | `/api/v1/public/hotels` | `PublicHotelsView` | `public-hotels` |
| `GET` | `/api/v1/public/hotels/detail` | `PublicHotelDetailView` | `public-hotel-detail` |
| `GET` | `/api/v1/public/hotels/reviews` | `PublicHotelReviewsView` | `public-hotel-reviews` |
| `GET` | `/api/v1/public/hotels/search-suggest` | `PublicHotelSearchSuggestView` | `public-hotels-search-suggest` |
| `GET` | `/api/v1/public/room-types/calendar` | `PublicRoomTypeCalendarView` | `public-room-type-calendar` |

## User

| Method | Path | View | Name |
|---|---|---|---|
| `POST` | `/api/v1/user/ai/chat` | `UserAIChatView` | `user-ai-chat` |
| `POST` | `/api/v1/user/ai/chat/stream` | `UserAIChatStreamView` | `user-ai-chat-stream` |
| `POST` | `/api/v1/user/ai/hotel-compare` | `UserAIHotelCompareView` | `user-ai-hotel-compare` |
| `POST` | `/api/v1/user/ai/recommendations` | `UserAIRecommendationsView` | `user-ai-recommendations` |
| `GET,POST` | `/api/v1/user/ai/sessions` | `UserAISessionsView` | `user-ai-sessions` |
| `GET` | `/api/v1/user/ai/sessions/<int:session_id>/messages` | `UserAISessionMessagesView` | `user-ai-session-messages` |
| `POST` | `/api/v1/user/auth/logout` | `LogoutApiView` | `user-logout` |
| `GET` | `/api/v1/user/auth/me` | `UserAuthMeView` | `user-auth-me` |
| `GET` | `/api/v1/user/coupons` | `UserCouponsView` | `user-coupons` |
| `GET` | `/api/v1/user/coupons/available` | `UserAvailableCouponsView` | `user-coupons-available` |
| `POST` | `/api/v1/user/coupons/claim` | `UserClaimCouponView` | `user-coupons-claim` |
| `GET,POST` | `/api/v1/user/favorites` | `UserFavoritesView` | `user-favorites` |
| `GET,POST` | `/api/v1/user/favorites/add` | `UserFavoritesView` | `user-favorites-add` |
| `GET,POST` | `/api/v1/user/favorites/remove` | `UserFavoritesView` | `user-favorites-remove` |
| `GET` | `/api/v1/user/invoices` | `UserInvoicesView` | `user-invoices` |
| `POST` | `/api/v1/user/invoices/apply` | `UserInvoiceApplyView` | `user-invoices-apply` |
| `POST` | `/api/v1/user/invoices/create` | `UserInvoiceTitleCreateView` | `user-invoices-create` |
| `DELETE,GET,POST` | `/api/v1/user/notices` | `UserNoticesView` | `user-notices` |
| `GET` | `/api/v1/user/notices/unread-count` | `UserNoticeUnreadCountView` | `user-notices-unread-count` |
| `GET` | `/api/v1/user/orders` | `UserOrdersView` | `user-orders` |
| `GET` | `/api/v1/user/orders/available-coupons` | `UserOrderAvailableCouponsView` | `user-orders-available-coupons` |
| `POST` | `/api/v1/user/orders/cancel` | `UserOrdersCancelView` | `user-orders-cancel` |
| `POST` | `/api/v1/user/orders/create` | `UserOrdersCreateView` | `user-orders-create` |
| `GET` | `/api/v1/user/orders/detail` | `UserOrdersDetailView` | `user-orders-detail` |
| `GET` | `/api/v1/user/orders/guest-history` | `UserOrderGuestHistoryView` | `user-order-guest-history` |
| `POST` | `/api/v1/user/orders/pay` | `UserOrdersPayView` | `user-orders-pay` |
| `POST` | `/api/v1/user/orders/update` | `UserOrdersUpdateView` | `user-orders-update` |
| `GET` | `/api/v1/user/points/logs` | `UserPointsLogsView` | `user-points-logs` |
| `GET,POST` | `/api/v1/user/profile` | `UserProfileView` | `user-profile` |
| `POST` | `/api/v1/user/profile/avatar` | `UserProfileAvatarView` | `user-profile-avatar` |
| `POST` | `/api/v1/user/profile/change-password` | `UserPasswordChangeView` | `user-profile-change-password` |
| `GET,POST` | `/api/v1/user/profile/update` | `UserProfileView` | `user-profile-update` |
| `GET` | `/api/v1/user/reviews` | `UserReviewsListView` | `user-reviews-list` |
| `POST` | `/api/v1/user/reviews/create` | `UserReviewsCreateView` | `user-reviews-create` |

## Admin

| Method | Path | View | Name |
|---|---|---|---|
| `POST` | `/api/v1/admin/ai/anomaly-report` | `AdminAIAnomalyReportView` | `admin-ai-anomaly-report` |
| `POST` | `/api/v1/admin/ai/business-report` | `AdminAIBusinessReportView` | `admin-ai-business-report` |
| `POST` | `/api/v1/admin/ai/business-report/stream` | `AdminAIBusinessReportStreamView` | `admin-ai-business-report-stream` |
| `GET` | `/api/v1/admin/ai/call-logs` | `AdminAICallLogsView` | `admin-ai-call-logs` |
| `POST` | `/api/v1/admin/ai/content-generate` | `AdminAIContentGenerateView` | `admin-ai-content-generate` |
| `POST` | `/api/v1/admin/ai/marketing-copy` | `AdminAIMarketingCopyView` | `admin-ai-marketing-copy` |
| `POST` | `/api/v1/admin/ai/order-anomaly-summary` | `AdminAIOrderAnomalySummaryView` | `admin-ai-order-anomaly-summary` |
| `POST` | `/api/v1/admin/ai/pricing-suggestion` | `AdminAIPricingSuggestionView` | `admin-ai-pricing-suggestion` |
| `POST` | `/api/v1/admin/ai/provider/add` | `AdminAIProviderAddView` | `admin-ai-provider-add` |
| `POST` | `/api/v1/admin/ai/provider/delete` | `AdminAIProviderDeleteView` | `admin-ai-provider-delete` |
| `POST` | `/api/v1/admin/ai/provider/switch` | `AdminAIProviderSwitchView` | `admin-ai-provider-switch` |
| `POST` | `/api/v1/admin/ai/reply-suggestion` | `AdminAIReplySuggestionView` | `admin-ai-reply-suggestion` |
| `POST` | `/api/v1/admin/ai/report-summary` | `AdminAIReportSummaryView` | `admin-ai-report-summary` |
| `POST` | `/api/v1/admin/ai/review-sentiment` | `AdminAIReviewSentimentView` | `admin-ai-review-sentiment` |
| `POST` | `/api/v1/admin/ai/review-summary` | `AdminAIReviewSummaryView` | `admin-ai-review-summary` |
| `GET,POST` | `/api/v1/admin/ai/settings` | `AdminAISettingsView` | `admin-ai-settings` |
| `GET,POST` | `/api/v1/admin/ai/settings/update` | `AdminAISettingsView` | `admin-ai-settings-update` |
| `GET` | `/api/v1/admin/ai/usage-stats` | `AdminAIUsageStatsView` | `admin-ai-usage-stats` |
| `GET,POST` | `/api/v1/admin/coupons` | `AdminCouponTemplatesView` | `admin-coupons` |
| `GET,POST` | `/api/v1/admin/coupons/create` | `AdminCouponTemplatesView` | `admin-coupons-create` |
| `POST` | `/api/v1/admin/coupons/update` | `AdminCouponTemplateUpdateView` | `admin-coupons-update` |
| `GET` | `/api/v1/admin/dashboard/charts` | `AdminDashboardChartsView` | `admin-dashboard-charts` |
| `GET` | `/api/v1/admin/dashboard/overview` | `AdminDashboardOverviewView` | `admin-dashboard-overview` |
| `GET,POST` | `/api/v1/admin/employees` | `AdminEmployeesView` | `admin-employees` |
| `GET,POST` | `/api/v1/admin/employees/create` | `AdminEmployeesView` | `admin-employees-create` |
| `GET,POST` | `/api/v1/admin/hotels` | `AdminHotelsView` | `admin-hotels` |
| `GET,POST` | `/api/v1/admin/hotels/create` | `AdminHotelsView` | `admin-hotels-create` |
| `GET,POST` | `/api/v1/admin/hotels/delete` | `AdminHotelsView` | `admin-hotels-delete` |
| `GET,POST` | `/api/v1/admin/hotels/update` | `AdminHotelsView` | `admin-hotels-update` |
| `GET,POST` | `/api/v1/admin/inventory/calendar` | `AdminInventoryView` | `admin-inventory-calendar` |
| `GET,POST` | `/api/v1/admin/inventory/update` | `AdminInventoryView` | `admin-inventory-update` |
| `GET` | `/api/v1/admin/members/overview` | `AdminMemberOverviewView` | `admin-members-overview` |
| `GET` | `/api/v1/admin/orders` | `AdminOrdersView` | `admin-orders` |
| `POST` | `/api/v1/admin/orders/change-status` | `AdminOrdersChangeStatusView` | `admin-orders-change-status` |
| `POST` | `/api/v1/admin/orders/check-in` | `AdminOrdersCheckInView` | `admin-orders-check-in` |
| `POST` | `/api/v1/admin/orders/check-out` | `AdminOrdersCheckOutView` | `admin-orders-check-out` |
| `GET` | `/api/v1/admin/orders/detail` | `AdminOrdersDetailView` | `admin-orders-detail` |
| `GET,POST` | `/api/v1/admin/reports/tasks` | `AdminReportTasksView` | `admin-report-tasks` |
| `GET,POST` | `/api/v1/admin/reports/tasks/create` | `AdminReportTasksView` | `admin-report-tasks-create` |
| `GET` | `/api/v1/admin/reviews` | `AdminReviewsView` | `admin-reviews` |
| `POST` | `/api/v1/admin/reviews/delete` | `AdminReviewDeleteView` | `admin-reviews-delete` |
| `POST` | `/api/v1/admin/reviews/reply` | `AdminReviewsReplyView` | `admin-reviews-reply` |
| `GET,POST` | `/api/v1/admin/room-types` | `AdminRoomTypesView` | `admin-room-types` |
| `GET,POST` | `/api/v1/admin/room-types/create` | `AdminRoomTypesView` | `admin-room-types-create` |
| `GET,POST` | `/api/v1/admin/room-types/delete` | `AdminRoomTypesView` | `admin-room-types-delete` |
| `GET,POST` | `/api/v1/admin/room-types/update` | `AdminRoomTypesView` | `admin-room-types-update` |
| `GET,POST` | `/api/v1/admin/settings` | `AdminSettingsView` | `admin-settings` |
| `GET,POST` | `/api/v1/admin/settings/update` | `AdminSettingsView` | `admin-settings-update` |
| `POST` | `/api/v1/admin/system/reset` | `AdminSystemResetView` | `admin-system-reset` |
| `GET` | `/api/v1/admin/system/status` | `AdminSystemStatusView` | `admin-system-status` |
| `GET` | `/api/v1/admin/users` | `AdminUsersView` | `admin-users` |
| `POST` | `/api/v1/admin/users/change-status` | `AdminUsersChangeStatusView` | `admin-users-change-status` |
