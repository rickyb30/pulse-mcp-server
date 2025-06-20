# GitHub Actions Workflows

## AI-Powered PR Summary Workflow

### Overview

The `pr-summary.yml` workflow automatically generates comprehensive AI-powered summaries for pull requests using OpenAI's GPT-4o-mini model. This helps with code review, documentation, and understanding the impact of changes.

### Features

🤖 **AI-Generated Summaries**: Creates detailed summaries based on:
- Commit messages and history
- Changed files and their content
- Code diffs and patches
- PR title and description

📊 **Automatic Statistics**: Provides metrics including:
- Number of files changed
- Lines added/deleted
- Commit count
- File type breakdown

🏷️ **Smart Labeling**: Automatically adds relevant labels:
- **Language tags**: `python`, `javascript`, etc.
- **Size labels**: `size/S`, `size/M`, `size/L`, `size/XL`
- **Category labels**: `documentation`, `configuration`, `ci/cd`
- **Project-specific**: `mcp`, `aws`

### Setup Instructions

#### 1. Add OpenAI API Key

1. Go to your repository's **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `OPENAI_API_KEY`
4. Value: Your OpenAI API key (get one from [OpenAI Platform](https://platform.openai.com/api-keys))

#### 2. Required Permissions

The workflow requires these permissions (already configured):
- `contents: read` - To access repository content
- `pull-requests: write` - To add comments and labels

#### 3. Workflow Triggers

The workflow automatically runs when:
- A new pull request is opened
- New commits are pushed to an existing PR
- A PR is reopened

### What the Workflow Does

#### Step 1: Gather PR Information
- Fetches PR details (title, description)
- Retrieves all commits in the PR
- Gets list of changed files with their diffs

#### Step 2: Generate AI Summary
- Sends structured data to OpenAI GPT-4o-mini
- Requests analysis covering:
  - **Summary**: Overview of changes
  - **Key Changes**: Main modifications and impact
  - **Technical Details**: Implementation specifics
  - **Testing Considerations**: What should be tested
  - **Potential Impact**: Affected areas

#### Step 3: Update PR
- Posts/updates a comment with the AI-generated summary
- Includes PR statistics and commit history
- Uses a special marker to identify AI comments

#### Step 4: Smart Labeling
- Analyzes file types and content
- Adds appropriate labels automatically
- Helps with organization and filtering

### Example Output

The workflow will create a comment like this:

```markdown
## 🤖 AI-Generated PR Summary

### Summary
This PR implements a new MCP server integration for VSCode, enabling direct interaction with AWS cost analysis tools through Copilot Chat.

### Key Changes
- Added `.vscode/mcp.json` configuration for MCP server
- Updated README with VSCode integration instructions
- Configured Pulse MCP server with stdio transport

### Technical Details
The implementation uses the Model Context Protocol to bridge VSCode Copilot with the existing Pulse server, enabling natural language queries for AWS cost analysis.

### Testing Considerations
- Verify MCP server starts correctly in VSCode
- Test tool availability in Copilot Agent Mode
- Validate AWS credential handling

### Potential Impact
- Enhances developer experience with AI-powered cost analysis
- May affect VSCode startup time if server initialization is slow

---

### 📊 PR Statistics
- **Files changed:** 2
- **Total additions:** 34
- **Total deletions:** 3
- **Commits:** 1

### 📝 Commit History
- `33e351f`: Add VSCode MCP configuration and update README
```

### Customization Options

#### Modify AI Model
Change the model in the workflow:
```yaml
model: 'gpt-4o-mini'  # or 'gpt-4', 'gpt-3.5-turbo'
```

#### Adjust Summary Length
Modify the `max_tokens` parameter:
```yaml
max_tokens: 1500  # Increase for longer summaries
```

#### Custom Labels
Add project-specific labels in the labeling step:
```yaml
if (prData.files.some(f => f.filename.includes('your-keyword'))) {
  labels.push('your-label');
}
```

#### Different AI Provider
Replace the OpenAI API call with other providers like:
- Anthropic Claude
- Google Gemini
- Azure OpenAI
- Local models

### Troubleshooting

#### Common Issues

1. **Missing OpenAI API Key**
   - Error: `OpenAI API error: 401`
   - Solution: Add `OPENAI_API_KEY` to repository secrets

2. **Rate Limiting**
   - Error: `OpenAI API error: 429`
   - Solution: Add delays or use different pricing tier

3. **Large PRs**
   - Error: Token limit exceeded
   - Solution: Reduce `max_tokens` or filter file content

4. **Permission Issues**
   - Error: Cannot create comment
   - Solution: Check repository permissions and workflow permissions

#### Debug Mode

Add debug logging to the workflow:
```yaml
- name: Debug PR Data
  run: |
    echo "PR Data: ${{ steps.pr-details.outputs.result }}"
```

### Cost Considerations

- OpenAI API usage depends on:
  - Number of PRs
  - Size of changes
  - Token usage per request
- Estimated cost: ~$0.01-0.05 per PR summary
- Monitor usage in OpenAI dashboard

### Security Notes

- API key is stored securely in GitHub Secrets
- No sensitive code is sent to OpenAI (only diffs and metadata)
- Comments are public if repository is public
- Consider using self-hosted runners for private code

### Contributing

To improve the workflow:
1. Fork the repository
2. Modify `.github/workflows/pr-summary.yml`
3. Test with a pull request
4. Submit improvements via PR 