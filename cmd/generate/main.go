package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"sort"
	"strings"

	"gopkg.in/yaml.v3"
)

type Project struct {
	Type        string    `yaml:"type"`
	Name        string    `yaml:"name,omitempty"`
	URL         string    `yaml:"url,omitempty"`
	DescEn      string    `yaml:"desc_en,omitempty"`
	DescZh      string    `yaml:"desc_zh,omitempty"`
	Stars       int       `yaml:"stars"`
	SubProjects []Project `yaml:"sub_projects,omitempty"`
}

type Group struct {
	Type     string    `yaml:"type"`
	HeaderEn string    `yaml:"header_en"`
	HeaderZh string    `yaml:"header_zh"`
	Projects []Project `yaml:"projects"`
}

type Text struct {
	Type   string `yaml:"type"`
	TextEn string `yaml:"text_en"`
	TextZh string `yaml:"text_zh"`
}

type Category struct {
	TitleEn string                   `yaml:"title_en"`
	TitleZh string                   `yaml:"title_zh"`
	Items   []map[string]interface{} `yaml:"items"`
}

func getStars(repoURL string, token string) int {
	re := regexp.MustCompile(`https://github\.com/([^/]+/[^/]+)`)
	matches := re.FindStringSubmatch(repoURL)
	if len(matches) > 1 {
		repo := strings.TrimRight(matches[1], "/")
		apiURL := fmt.Sprintf("https://api.github.com/repos/%s", repo)
		req, err := http.NewRequest("GET", apiURL, nil)
		if err != nil {
			log.Printf("Error creating request for %s: %v\n", repo, err)
			return 0
		}
		if token != "" {
			req.Header.Set("Authorization", "token "+token)
		}
		req.Header.Set("Accept", "application/vnd.github.v3+json")

		client := &http.Client{}
		resp, err := client.Do(req)
		if err != nil {
			log.Printf("Error fetching stars for %s: %v\n", repo, err)
			return 0
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			log.Printf("Non-OK HTTP status for %s: %s\n", repo, resp.Status)
			return 0
		}

		body, err := io.ReadAll(resp.Body)
		if err != nil {
			log.Printf("Error reading response for %s: %v\n", repo, err)
			return 0
		}

		var data map[string]interface{}
		if err := json.Unmarshal(body, &data); err != nil {
			log.Printf("Error decoding JSON for %s: %v\n", repo, err)
			return 0
		}

		if stars, ok := data["stargazers_count"].(float64); ok {
			return int(stars)
		}
	}
	return 0
}

func main() {
	updateStars := flag.Bool("update-stars", false, "Update GitHub stars")
	flag.Parse()

	token := os.Getenv("GITHUB_TOKEN")

	data, err := os.ReadFile("meta/projects.yml")
	if err != nil {
		log.Fatalf("Error reading meta/projects.yml: %v", err)
	}

	var categories []Category
	if err := yaml.Unmarshal(data, &categories); err != nil {
		log.Fatalf("Error unmarshaling YAML: %v", err)
	}
	if len(categories) == 0 {
		log.Println("Warning: projects.yml is empty or parsed as empty.")
	}

	decodeItem := func(m map[string]interface{}) (string, interface{}) {
		t, _ := m["type"].(string)
		var item interface{}
		b, _ := yaml.Marshal(m)
		switch t {
		case "project":
			var p Project
			yaml.Unmarshal(b, &p)
			item = p
		case "group":
			var g Group
			yaml.Unmarshal(b, &g)
			item = g
		case "text":
			var tx Text
			yaml.Unmarshal(b, &tx)
			item = tx
		}
		return t, item
	}

	for i, cat := range categories {
		if *updateStars {
			for j, m := range cat.Items {
				t, item := decodeItem(m)
				if t == "project" {
					p := item.(Project)
					p.Stars = getStars(p.URL, token)
					for k := range p.SubProjects {
						p.SubProjects[k].Stars = getStars(p.SubProjects[k].URL, token)
					}
					b, _ := yaml.Marshal(p)
					yaml.Unmarshal(b, &cat.Items[j])
				} else if t == "group" {
					g := item.(Group)
					for k := range g.Projects {
						g.Projects[k].Stars = getStars(g.Projects[k].URL, token)
						for l := range g.Projects[k].SubProjects {
							g.Projects[k].SubProjects[l].Stars = getStars(g.Projects[k].SubProjects[l].URL, token)
						}
					}
					b, _ := yaml.Marshal(g)
					yaml.Unmarshal(b, &cat.Items[j])
				}
			}
		}

		var projectsAndGroups []map[string]interface{}
		var texts []map[string]interface{}

		for _, m := range cat.Items {
			t, item := decodeItem(m)
			if t == "project" {
				p := item.(Project)
				sort.Slice(p.SubProjects, func(a, b int) bool {
					return p.SubProjects[a].Stars > p.SubProjects[b].Stars
				})
				b, _ := yaml.Marshal(p)
				var newM map[string]interface{}
				yaml.Unmarshal(b, &newM)
				projectsAndGroups = append(projectsAndGroups, newM)
			} else if t == "group" {
				g := item.(Group)
				sort.Slice(g.Projects, func(a, b int) bool {
					return g.Projects[a].Stars > g.Projects[b].Stars
				})
				for k := range g.Projects {
					sort.Slice(g.Projects[k].SubProjects, func(a, b int) bool {
						return g.Projects[k].SubProjects[a].Stars > g.Projects[k].SubProjects[b].Stars
					})
				}
				b, _ := yaml.Marshal(g)
				var newM map[string]interface{}
				yaml.Unmarshal(b, &newM)
				projectsAndGroups = append(projectsAndGroups, newM)
			} else {
				texts = append(texts, m)
			}
		}

		sort.SliceStable(projectsAndGroups, func(a, b int) bool {
			ta, itemA := decodeItem(projectsAndGroups[a])
			tb, itemB := decodeItem(projectsAndGroups[b])

			getStars := func(t string, item interface{}) int {
				if t == "project" {
					return item.(Project).Stars
				} else if t == "group" {
					max := 0
					g := item.(Group)
					for _, p := range g.Projects {
						if p.Stars > max {
							max = p.Stars
						}
					}
					return max
				}
				return 0
			}
			return getStars(ta, itemA) > getStars(tb, itemB)
		})

		categories[i].Items = append(projectsAndGroups, texts...)
	}

	if *updateStars {
		out, err := yaml.Marshal(categories)
		if err != nil {
			log.Fatalf("Error marshaling YAML: %v", err)
		}
		os.WriteFile("meta/projects.yml", out, 0644)
	}

	generateReadme(categories, "en", "README.md", "template/README.md.tmpl")
	generateReadme(categories, "zh", "README.zh-CN.md", "template/README.zh-CN.md.tmpl")
}

func generateReadme(categories []Category, lang, filename, tmplFilename string) {
	var lines []string

	lines = append(lines, "<!-- BEGIN AUTOMATED SECTION -->")

	for _, cat := range categories {
		title := cat.TitleEn
		if lang == "zh" && cat.TitleZh != "" {
			title = cat.TitleZh
		}

		lines = append(lines, "### "+title)
		lines = append(lines, "")

		var renderProject func(p Project, isSub bool)
		renderProject = func(p Project, isSub bool) {
			desc := p.DescEn
			if lang == "zh" && p.DescZh != "" {
				desc = p.DescZh
			}
			descStr := ""
			if desc != "" {
				desc = strings.TrimSpace(desc)
				if lang == "zh" {
					if strings.HasPrefix(desc, "，") || strings.HasPrefix(desc, "。") || strings.HasPrefix(desc, "（") {
						descStr = desc
					} else {
						descStr = " " + desc
					}
				} else {
					if strings.HasPrefix(desc, ",") {
						descStr = desc
					} else {
						descStr = " " + desc
					}
				}
			}
			prefix := ""
			if isSub {
				prefix = "* "
			}
			lines = append(lines, fmt.Sprintf("%s[%s](%s)%s", prefix, p.Name, p.URL, descStr))
			if !isSub && len(p.SubProjects) == 0 {
				lines = append(lines, "")
			}
			for _, sp := range p.SubProjects {
				renderProject(sp, true)
			}
			if len(p.SubProjects) > 0 && !isSub {
				lines = append(lines, "")
			}
		}

		for _, m := range cat.Items {
			t, _ := m["type"].(string)
			b, _ := yaml.Marshal(m)
			switch t {
			case "project":
				var p Project
				yaml.Unmarshal(b, &p)
				renderProject(p, false)
			case "group":
				var g Group
				yaml.Unmarshal(b, &g)
				header := g.HeaderEn
				if lang == "zh" && g.HeaderZh != "" {
					header = g.HeaderZh
				}
				lines = append(lines, header)
				for _, p := range g.Projects {
					renderProject(p, true)
				}
				lines = append(lines, "")
			case "text":
				var tx Text
				yaml.Unmarshal(b, &tx)
				text := tx.TextEn
				if lang == "zh" && tx.TextZh != "" {
					text = tx.TextZh
				}
				if strings.Contains(text, "BTW, if you have interests") || strings.Contains(text, "顺便说一句") {
					continue
				}
				if strings.Contains(text, "<!-- END AUTOMATED SECTION -->") || strings.Contains(text, "<!-- BEGIN AUTOMATED SECTION -->") {
					continue
				}
				if strings.HasPrefix(text, "[tcell]") && strings.Contains(text, "Awesome Go") {
					continue
				}

				lines = append(lines, text)
				lines = append(lines, "")
			}
		}
	}

	lines = append(lines, "<!-- END AUTOMATED SECTION -->")

	automatedContent := strings.TrimSpace(strings.Join(lines, "\n"))

	tmplBytes, err := os.ReadFile(tmplFilename)
	if err != nil {
		log.Fatalf("Error reading %s: %v", tmplFilename, err)
	}
	content := string(tmplBytes)

	content = strings.Replace(content, "{{CONTENT}}", automatedContent, 1)

	err = os.WriteFile(filename, []byte(content), 0644)
	if err != nil {
		log.Fatalf("Error writing %s: %v", filename, err)
	}
}
