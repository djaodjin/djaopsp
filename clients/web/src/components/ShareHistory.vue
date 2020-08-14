<template>
  <div class="pa-6" v-if="!history.length">
    <p class="text-subtitle-1 text-center">
      The assessment has not yet been shared with any organizations.
    </p>
  </div>
  <div v-else>
    <p>{{ $t('share.tab2.intro') }}</p>
    <v-text-field
      v-model="search"
      append-icon="mdi-magnify"
      label="Search"
      single-line
      hide-details
    ></v-text-field>
    <v-data-table
      class="share-history"
      multi-sort
      hide-default-footer
      :mobile-breakpoint="-1"
      :sort-by="['date']"
      :sort-desc="[true]"
      :headers="headers"
      :items="history"
      :items-per-page="history.length"
      :search="search"
    >
      <template v-slot:item.date="{ item, value }">
        <span v-format-date>{{ value }}</span>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import { formatDate } from '@/directives'

export default {
  name: 'ShareHistory',

  props: ['history'],

  data() {
    return {
      search: '',
      headers: [
        {
          text: 'Date',
          filterable: false,
          value: 'date',
        },
        { text: 'Organization', value: 'organization.name' },
      ],
    }
  },

  directives: {
    formatDate,
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.share-history ::v-deep table {
  margin-top: 16px;

  th {
    background-color: $background-table-header;
  }

  tr:nth-child(even) {
    background-color: $background-row-alternate;
  }
}
</style>
