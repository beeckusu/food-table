# Epic: Encyclopedia Placeholder/Stub Entries for Similar Dishes

## Epic Summary
Add support for placeholder/stub entries in the Encyclopedia system to allow quick referencing of similar dishes without requiring a full entry to be written immediately.

## Problem Statement
Currently, the Similar Dishes feature in Encyclopedia entries requires linking to complete Encyclopedia entries with full descriptions, history, and other detailed content. However, when documenting a dish, users often know of similar dishes but aren't ready to commit to writing full entries for them yet. This creates friction in the documentation process and results in incomplete similarity mappings.

## User Stories

### As an Admin User
- **US-1**: As an admin, I want to create placeholder entries with just a name so that I can quickly note similar dishes without writing full entries
- **US-2**: As an admin, I want to see visual indicators on placeholder entries so that I know which entries need to be completed
- **US-3**: As an admin, I want to click on a placeholder entry and be prompted to create the full entry so that I can easily convert stubs to complete entries
- **US-4**: As an admin, I want to link encyclopedia entries to both full entries and placeholder entries as similar dishes so that I can build comprehensive similarity networks incrementally

### As a Regular User
- **US-5**: As a regular user, I want to see the names of similar dishes (including placeholders) so that I can discover related dishes
- **US-6**: As a regular user, I should not be able to click on placeholder entries since they have no content to view

## Acceptance Criteria

### Core Functionality
- [ ] Placeholder entries can be created with only a name field (all other fields optional/empty)
- [ ] Placeholder entries can be linked as similar dishes to regular encyclopedia entries
- [ ] Placeholder entries have a flag/field to distinguish them from complete entries
- [ ] The similar dishes ManyToManyField accepts both regular and placeholder entries

### UI/UX - Admin View
- [ ] Admin can create placeholder entries from the Django admin interface
- [ ] Admin can create placeholder entries directly when selecting similar dishes
- [ ] Placeholder entries in the Similar Dishes section display with a visual indicator (e.g., badge, italics, or icon)
- [ ] Clicking a placeholder entry as admin shows a prompt/modal to create the full entry
- [ ] The create prompt pre-fills the name from the placeholder
- [ ] Admin can distinguish placeholders from complete entries in list views

### UI/UX - Regular User View
- [ ] Regular users see placeholder names in the Similar Dishes section
- [ ] Placeholder entries display as plain text (non-clickable) for regular users
- [ ] Visual distinction indicates incomplete status without admin-specific language

### Data Management
- [ ] When converting a placeholder to full entry, the placeholder is upgraded (not replaced)
- [ ] All existing links to the placeholder are maintained during conversion
- [ ] Deleting a placeholder shows warning if it's referenced as a similar dish
- [ ] Search functionality clearly indicates placeholder vs. complete entries

## Technical Considerations

### Database Schema
**Option A**: Add boolean flag to existing Encyclopedia model
```python
is_placeholder = models.BooleanField(default=False)
```

**Option B**: Create separate EncyclopediaPlaceholder model
```python
class EncyclopediaPlaceholder(models.Model):
    name = models.CharField(max_length=255)
    # Minimal fields only
```

**Recommendation**: Option A - simpler implementation, easier migration path, maintains referential integrity

### Model Changes
1. Add `is_placeholder` field to Encyclopedia model
2. Update validation to allow empty description/content fields when `is_placeholder=True`
3. Add property method `is_complete` for clarity
4. Update `__str__` method to indicate placeholder status

### View Changes
1. Update `encyclopedia_detail.html` template:
   - Check `is_placeholder` flag in similar dishes loop
   - Conditionally render links based on user status
   - Add visual indicators for placeholders
2. Create new admin view/modal for "Create from Placeholder" workflow
3. Update encyclopedia create API to support placeholder creation

### Admin Interface
1. Add filter for showing placeholders in list view
2. Add inline action to convert placeholder to full entry
3. Add "Create Placeholder" quick action
4. Show placeholder count in admin statistics

### Migration Strategy
1. Add `is_placeholder` field with default=False to Encyclopedia
2. Existing entries remain unchanged
3. Add database index on `is_placeholder` for filtering

## Implementation Approach

### Phase 1: Database & Model Layer (Story 1)
- Add `is_placeholder` field to Encyclopedia model
- Update model validation logic
- Create database migration
- Add model tests

### Phase 2: Admin Interface (Story 2)
- Update Django admin to support placeholder creation
- Add filters and list display indicators
- Add inline editing capabilities
- Add admin-specific tests

### Phase 3: Frontend Display (Story 3)
- Update encyclopedia detail template
- Add visual indicators for placeholders
- Implement conditional rendering based on user type
- Add frontend tests

### Phase 4: Conversion Workflow (Story 4)
- Create "Convert to Full Entry" view/modal
- Add prompt when admin clicks placeholder
- Pre-populate creation form with placeholder data
- Add integration tests

## Edge Cases & Considerations

1. **Duplicate Names**: How to handle placeholders with same name as existing entries?
   - Solution: Slugify with incrementing suffix, or show warning in admin

2. **Orphaned Placeholders**: Placeholders never converted to full entries
   - Solution: Add admin report for old unused placeholders

3. **Search Behavior**: Should placeholders appear in encyclopedia search?
   - Recommendation: Yes, but with clear indicator

4. **API Access**: How should API return placeholders?
   - Solution: Include `is_placeholder` flag in serialized data

5. **Circular References**: Placeholder as similar dish to itself
   - Solution: Existing validation should prevent this

6. **Performance**: Impact on queries with many placeholders
   - Solution: Add database index on `is_placeholder` field

7. **Migration Path**: Users with many placeholders
   - Solution: Bulk conversion tool in admin

## Related Code References
- Parent-child hierarchy: `content/models/encyclopedia.py:22-28`
- Similar dishes ManyToManyField: `content/models/encyclopedia.py:39-44`
- Encyclopedia admin interface: `content/admin/encyclopedia.py`
- Encyclopedia detail template: `templates/encyclopedia/detail.html:298-342`

## Success Metrics
- Admins can create placeholders in < 10 seconds
- Conversion from placeholder to full entry takes < 30 seconds
- No broken links when converting placeholders
- Regular users see placeholder names without confusion
- Admin adoption rate > 80% within first month

## Open Questions
1. Should placeholders be exportable/importable?
2. Should there be a limit on number of placeholders per entry?
3. Should placeholder creation be available to non-admin users?
4. Should email notifications be sent when placeholders are created?
